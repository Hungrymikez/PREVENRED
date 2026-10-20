"""Índices de capas del mapa. geometry debe ser GeoJSON para el 2dsphere."""
from pymongo.database import Database

from prevenred.shared.infrastructure.mongo import ensure_index

COLLECTION = "map_layers"


def ensure_indexes(db: Database) -> None:
    """Crea el índice geoespacial de las capas. Es idempotente."""
    ensure_index(
        db[COLLECTION],
        [("geometry", "2dsphere")],
        name="ix_map_layers_geometry_2dsphere",
    )
