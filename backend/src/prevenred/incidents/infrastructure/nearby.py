"""Consultas de incidentes cercanos sobre MongoDB real ($nearSphere)."""
from pymongo.database import Database

from prevenred.incidents.infrastructure.indexes import COLLECTION


def find_incidents_near(
    db: Database,
    longitude: float,
    latitude: float,
    max_distance_meters: int,
) -> list[dict]:
    """Devuelve incidentes ordenados por distancia al punto dado.

    Exige el índice 2dsphere de location (se crea al arrancar la aplicación).
    """
    return list(db[COLLECTION].find({
        "location": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": max_distance_meters,
            }
        }
    }))
