from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from usecasecore import PolicyDenied, TransitionDenied, ValidationFailed

from .database import create_engine_for_url, create_schema, create_session_factory
from .repositories import (
    SQLAlchemyAuditSink,
    SQLAlchemyIdempotencyStore,
    SQLAlchemyInventoryRepository,
    SQLAlchemyOutboxEventBus,
    SQLAlchemyOutboxJobQueue,
)
from .schemas import MoveInventoryRequest, MoveInventoryResponse
from .transaction import SQLAlchemyTransactionManager
from .usecases import MoveInventoryUseCase


def create_app(
    *,
    database_url: str = "sqlite+pysqlite:///:memory:",
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    if session_factory is None:
        engine = create_engine_for_url(database_url)
        create_schema(engine)
        session_factory = create_session_factory(engine)

    app = FastAPI(title="UseCaseCore FastAPI SQLAlchemy Inventory Example")
    app.state.session_factory = session_factory

    def get_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    @app.post("/inventory/move", response_model=MoveInventoryResponse)
    def move_inventory(
        request: MoveInventoryRequest,
        session: Session = Depends(get_session),  # noqa: B008
    ) -> MoveInventoryResponse:
        use_case = MoveInventoryUseCase(
            repository=SQLAlchemyInventoryRepository(session),
            idempotency_store=SQLAlchemyIdempotencyStore(session),
            audit_sink=SQLAlchemyAuditSink(session),
            event_bus=SQLAlchemyOutboxEventBus(session),
            job_queue=SQLAlchemyOutboxJobQueue(session),
            transaction_manager=SQLAlchemyTransactionManager(session),
        )

        try:
            result = use_case.execute(request.to_command())
        except ValidationFailed as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PolicyDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except TransitionDenied as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return MoveInventoryResponse.from_result(result)

    return app


app = create_app()
