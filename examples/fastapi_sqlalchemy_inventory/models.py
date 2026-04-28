from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    product_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    bin_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    low_stock_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    movement_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    product_id: Mapped[str] = mapped_column(String(100), nullable=False)
    from_bin_id: Mapped[str] = mapped_column(String(100), nullable=False)
    to_bin_id: Mapped[str] = mapped_column(String(100), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    moved_by_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OutboxRecord(Base):
    __tablename__ = "outbox_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
