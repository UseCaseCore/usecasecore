from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from usecasecore.audit import AuditEntry

from .models import (
    AuditRecord,
    IdempotencyRecord,
    InventoryBalance,
    InventoryMovement,
    OutboxRecord,
)
from .usecases import MoveInventoryCommand, MoveInventoryResult


class SQLAlchemyInventoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_balance_for_update(
        self,
        product_id: str,
        bin_id: str,
    ) -> InventoryBalance | None:
        statement = (
            select(InventoryBalance)
            .where(
                InventoryBalance.product_id == product_id,
                InventoryBalance.bin_id == bin_id,
            )
            .with_for_update()
        )
        return self.session.execute(statement).scalar_one_or_none()

    def move(
        self,
        command: MoveInventoryCommand,
        source: InventoryBalance,
        destination: InventoryBalance,
    ) -> tuple[InventoryMovement, InventoryBalance, InventoryBalance]:
        source.qty -= command.qty
        destination.qty += command.qty

        movement_number = self.session.scalar(
            select(func.count()).select_from(InventoryMovement)
        )
        movement_id = f"movement-{(movement_number or 0) + 1}"
        movement = InventoryMovement(
            movement_id=movement_id,
            request_id=command.request_id,
            product_id=command.product_id,
            from_bin_id=command.from_bin_id,
            to_bin_id=command.to_bin_id,
            qty=command.qty,
            moved_by_user_id=command.moved_by_user_id,
            reason=command.reason,
        )
        self.session.add(movement)
        self.session.flush()
        return movement, source, destination


class SQLAlchemyIdempotencyStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str) -> MoveInventoryResult | None:
        record = self.session.get(IdempotencyRecord, key)
        if record is None:
            return None

        return MoveInventoryResult(**json.loads(record.response_json))

    def save(self, key: str, result: object) -> None:
        response_json = json.dumps(asdict(result), sort_keys=True)
        existing = self.session.get(IdempotencyRecord, key)
        if existing is not None:
            existing.response_json = response_json
            return None

        self.session.add(IdempotencyRecord(key=key, response_json=response_json))


class SQLAlchemyAuditSink:
    def __init__(self, session: Session) -> None:
        self.session = session

    def write(self, entry: AuditEntry) -> None:
        self.session.add(
            AuditRecord(
                action=entry.action,
                actor_id=entry.actor_id,
                payload_json=json.dumps(dict(entry.payload), sort_keys=True),
            )
        )


class SQLAlchemyOutboxEventBus:
    def __init__(self, session: Session) -> None:
        self.session = session

    def publish(self, event: object) -> None:
        self._write_outbox(event)

    def _write_outbox(self, payload: object) -> None:
        self.session.add(
            OutboxRecord(
                event_type=type(payload).__name__,
                payload_json=json.dumps(to_payload(payload), sort_keys=True),
            )
        )


class SQLAlchemyOutboxJobQueue:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(self, job: object) -> None:
        self.session.add(
            OutboxRecord(
                event_type=type(job).__name__,
                payload_json=json.dumps(to_payload(job), sort_keys=True),
            )
        )


def to_payload(value: object) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        payload = asdict(value)
        return dict(payload)
    if isinstance(value, dict):
        return value
    return {"value": repr(value)}
