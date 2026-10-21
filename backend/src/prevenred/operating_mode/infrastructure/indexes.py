"""Índices de la colección `operational_modes` (docs/db/operational_modes.md)."""

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from .mongo_mode_repository import COLLECTION


def ensure_indexes(db: Database) -> None:
    """Crea índices idempotentes: un solo activo + historial por startedAt."""
    col = db[COLLECTION]
    # Único parcial: solo un documento con active=true.
    col.create_index(
        [("active", ASCENDING)],
        unique=True,
        partialFilterExpression={"active": True},
        name="ux_operational_modes_active",
    )
    col.create_index([("startedAt", DESCENDING)], name="ix_operational_modes_startedAt")
