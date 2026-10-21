"""Consultas de capas cercanas sobre MongoDB real ($nearSphere)."""
from pymongo.database import Database

from prevenred.geo.infrastructure.indexes import COLLECTION


def find_layers_near(
    db: Database,
    longitude: float,
    latitude: float,
    max_distance_meters: int,
) -> list[dict]:
    """Devuelve capas cuyo geometry está cerca del punto dado.

    Exige el índice 2dsphere de geometry (se crea al arrancar la aplicación).
    """
    return list(db[COLLECTION].find({
        "geometry": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": max_distance_meters,
            }
        }
    }))
