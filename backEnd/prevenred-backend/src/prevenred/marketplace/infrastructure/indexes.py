"""Índices del marketplace (reservas y operaciones). Se crean al arrancar (idempotente)."""
from pymongo.database import Database

from prevenred.marketplace.infrastructure.mongo_marketplace_repository import (
    RESERVATIONS,
    TRANSACTIONS,
)


def ensure_indexes(db: Database) -> None:
    """Crea los índices de `reservations` y `transactions` (CU-13, CU-14, CU-15)."""
    reservations = db[RESERVATIONS]
    # Choques de fechas: se resuelven con `toolId` + rango de fechas.
    reservations.create_index(
        [("toolId", 1), ("startDate", 1), ("endDate", 1)],
        name="ix_reservations_tool_dates",
    )
    reservations.create_index(
        [("requesterId", 1), ("createdAt", -1)], name="ix_reservations_requester"
    )
    reservations.create_index(
        [("ownerId", 1), ("status", 1), ("createdAt", -1)], name="ix_reservations_owner"
    )
    # Una misma persona no puede tener dos reservas idénticas para la misma
    # herramienta creadas en el mismo instante (protege reintentos del cliente).
    reservations.create_index(
        [("toolId", 1), ("requesterId", 1), ("createdAt", 1)],
        unique=True,
        name="uq_reservations_request",
    )

    transactions = db[TRANSACTIONS]
    transactions.create_index(
        [("buyerId", 1), ("createdAt", -1)], name="ix_transactions_buyer"
    )
    transactions.create_index(
        [("sellerId", 1), ("createdAt", -1)], name="ix_transactions_seller"
    )
    transactions.create_index(
        [("itemId", 1), ("status", 1)], name="ix_transactions_item_status"
    )
