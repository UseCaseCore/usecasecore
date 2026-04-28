from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from examples.fastapi_sqlalchemy_inventory.app import create_app
from examples.fastapi_sqlalchemy_inventory.database import (
    create_engine_for_url,
    create_schema,
    create_session_factory,
)
from examples.fastapi_sqlalchemy_inventory.models import (
    AuditRecord,
    IdempotencyRecord,
    InventoryBalance,
    InventoryMovement,
    OutboxRecord,
)


@pytest.fixture
def app_session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine_for_url("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = create_session_factory(engine)
    yield session_factory
    engine.dispose()


@pytest.fixture
def client(app_session_factory: sessionmaker[Session]) -> TestClient:
    app = create_app(session_factory=app_session_factory)
    return TestClient(app)


def seed_balances(
    session_factory: sessionmaker[Session],
    *,
    source_qty: int = 10,
    dest_qty: int | None = 1,
    low_stock_threshold: int | None = 6,
) -> None:
    with session_factory() as session:
        session.add(
            InventoryBalance(
                product_id="sku-1",
                bin_id="A",
                qty=source_qty,
                low_stock_threshold=low_stock_threshold,
            )
        )
        if dest_qty is not None:
            session.add(
                InventoryBalance(
                    product_id="sku-1",
                    bin_id="B",
                    qty=dest_qty,
                )
            )
        session.commit()


def move_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "request_id": "req-1",
        "idempotency_key": "move-sku-1-A-B-4",
        "product_id": "sku-1",
        "from_bin_id": "A",
        "to_bin_id": "B",
        "qty": 4,
        "moved_by_user_id": "user-1",
        "reason": "rebalancing",
    }
    payload.update(overrides)
    return payload


def count_rows(session: Session, model: type[object]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def get_balance(session: Session, product_id: str, bin_id: str) -> InventoryBalance | None:
    return session.get(InventoryBalance, {"product_id": product_id, "bin_id": bin_id})


def test_post_move_inventory_updates_state_and_records_side_effects(
    client: TestClient,
    app_session_factory: sessionmaker[Session],
) -> None:
    seed_balances(app_session_factory)

    response = client.post("/inventory/move", json=move_payload())

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "movement_id": "movement-1",
        "product_id": "sku-1",
        "from_bin_id": "A",
        "to_bin_id": "B",
        "quantity_moved": 4,
        "source_qty_after": 6,
        "dest_qty_after": 5,
    }

    with app_session_factory() as session:
        source = get_balance(session, "sku-1", "A")
        destination = get_balance(session, "sku-1", "B")
        assert source is not None
        assert destination is not None
        assert source.qty == 6
        assert destination.qty == 5

        movement = session.get(InventoryMovement, "movement-1")
        assert movement is not None
        assert movement.request_id == "req-1"

        assert count_rows(session, AuditRecord) == 1
        audit = session.scalars(select(AuditRecord)).one()
        assert audit.action == "MoveInventory"
        assert audit.actor_id == "user-1"
        assert json.loads(audit.payload_json)["movement_id"] == "movement-1"

        assert count_rows(session, OutboxRecord) == 2
        event_types = {record.event_type for record in session.scalars(select(OutboxRecord))}
        assert event_types == {"InventoryMoved", "LowStockAlert"}

        idempotency = session.get(IdempotencyRecord, "move-sku-1-A-B-4")
        assert idempotency is not None
        assert json.loads(idempotency.response_json)["movement_id"] == "movement-1"


def test_idempotency_replays_response_without_duplicate_writes(
    client: TestClient,
    app_session_factory: sessionmaker[Session],
) -> None:
    seed_balances(app_session_factory)
    payload = move_payload()

    first = client.post("/inventory/move", json=payload)
    second = client.post("/inventory/move", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()

    with app_session_factory() as session:
        source = get_balance(session, "sku-1", "A")
        destination = get_balance(session, "sku-1", "B")
        assert source is not None
        assert destination is not None
        assert source.qty == 6
        assert destination.qty == 5
        assert count_rows(session, InventoryMovement) == 1
        assert count_rows(session, AuditRecord) == 1
        assert count_rows(session, OutboxRecord) == 2
        assert count_rows(session, IdempotencyRecord) == 1


def test_invalid_qty_returns_400(
    client: TestClient,
    app_session_factory: sessionmaker[Session],
) -> None:
    seed_balances(app_session_factory)

    response = client.post("/inventory/move", json=move_payload(qty=0))

    assert response.status_code == 400
    assert response.json()["detail"] == "qty must be greater than zero"


def test_insufficient_inventory_returns_409(
    client: TestClient,
    app_session_factory: sessionmaker[Session],
) -> None:
    seed_balances(app_session_factory, source_qty=1)

    response = client.post("/inventory/move", json=move_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "source bin does not have enough inventory"


def test_missing_destination_returns_409(
    client: TestClient,
    app_session_factory: sessionmaker[Session],
) -> None:
    seed_balances(app_session_factory, dest_qty=None)

    response = client.post("/inventory/move", json=move_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "destination balance does not exist"
