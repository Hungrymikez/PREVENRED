"""Índices de la colección `property_inspections`."""

from pymongo import ASCENDING, GEOSPHERE
from pymongo.database import Database

from .mongo_fieldwork_repository import COLLECTION


def ensure_indexes(db: Database) -> None:
    """Crea índices idempotentes: 2dsphere, inspector, barrio."""
    col = db[COLLECTION]
    col.create_index([("location", GEOSPHERE)], name="ix_inspections_location_2dsphere")
    col.create_index("inspectorId", name="ix_inspections_inspectorId")
    col.create_index("neighborhood", name="ix_inspections_neighborhood")
    col.create_index(
        [("inspectorId", ASCENDING), ("inspectedAt", ASCENDING)],
        name="ix_inspections_inspector_inspectedAt",
    )
