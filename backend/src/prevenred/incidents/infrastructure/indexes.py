"""Índices de incidentes. El 2dsphere permite $nearSphere sobre location."""
from pymongo.database import Database

from prevenred.shared.infrastructure.mongo import ensure_index

COLLECTION = "incidents"


def ensure_indexes(db: Database) -> None:
    """Crea el índice geoespacial de reportes. Es idempotente."""
    ensure_index(
        db[COLLECTION],
        [("location", "2dsphere")],
        name="ix_incidents_location_2dsphere",
    )
