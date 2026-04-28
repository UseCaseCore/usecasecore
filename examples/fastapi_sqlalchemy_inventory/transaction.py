from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session


class SQLAlchemyTransactionManager:
    """Commit or roll back the SQLAlchemy session at the use-case boundary."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def __call__(self) -> SQLAlchemyTransaction:
        return SQLAlchemyTransaction(self.session)


class SQLAlchemyTransaction:
    def __init__(self, session: Session) -> None:
        self.session = session

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            self.session.rollback()
            return False

        self.session.commit()
        return False
