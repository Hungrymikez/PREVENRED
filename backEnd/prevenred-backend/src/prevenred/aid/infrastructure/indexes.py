"""Índices de aid (necesidades e inventario). Se crean al arrancar (idempotente)."""
from pymongo.database import Database

from prevenred.aid.infrastructure.mongo_aid_repository import (
    INVENTORY_COLLECTION,
    NEEDS_COLLECTION,
)


def ensure_indexes(db: Database) -> None:
    """Crea los índices de `aid_needs` y `aid_inventory` (CU-31, CU-41, CU-42)."""
    needs = db[NEEDS_COLLECTION]
    needs.create_index("caseId", unique=True, name="uq_aid_needs_case", sparse=True)
    needs.create_index("requestedBy", name="ix_aid_needs_requester")
    needs.create_index([("location", "2dsphere")], name="geo_aid_needs_location")
    needs.create_index(
        [("status", 1), ("priority", -1)], name="ix_aid_needs_status_priority"
    )

    inventory = db[INVENTORY_COLLECTION]
    inventory.create_index(
        [("sourceType", 1), ("sourceId", 1)], name="ix_aid_inventory_source"
    )
    inventory.create_index(
        [("status", 1), ("availableQuantity", 1), ("type", 1)],
        name="ix_aid_inventory_stock",
    )
