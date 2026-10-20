"""Índices de geo (capas del mapa). Se crean al arrancar la app (idempotente)."""
from pymongo.database import Database

from prevenred.geo.infrastructure.mongo_map_layer_repository import COLLECTION as LAYERS_COLLECTION


def ensure_indexes(db: Database) -> None:
    """Crea los índices de la colección `map_layers`."""
    layers = db[LAYERS_COLLECTION]
    # El nombre es único: dos capas con el mismo nombre confundirían al mapa.
    layers.create_index("name", unique=True, name="uq_map_layers_name")
    layers.create_index([("name", 1), ("version", 1)], name="ix_map_layers_name_version")
    # Filtro de visibilidad por rol (CU-10).
    layers.create_index("visibleForRoles", name="ix_map_layers_roles")
