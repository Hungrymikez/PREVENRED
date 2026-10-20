"""
Conexión a MongoDB con PyMongo (síncrono, sin ODM).

Decisión: sin ODM (Beanie/MongoEngine). Cada repositorio traduce a mano
documento <-> entidad; es poco código, deja el dominio limpio (DDD) y es lo más
fácil de pedirle a un LLM sin errores.

PyMongo conecta de forma perezosa: crear el cliente no falla aunque Mongo esté apagado;
el error aparece en la primera operación.
"""

from datetime import UTC, datetime
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from prevenred.shared.infrastructure.config import get_settings


@lru_cache
def get_client() -> MongoClient:
    """Cliente único de MongoDB (se crea una vez; conecta al primer uso)."""
    return MongoClient(get_settings().mongo_uri, tz_aware=True)


def get_db() -> Database:
    """Dependencia de FastAPI: la base de datos del proyecto.
    En las pruebas se reemplaza por una base en memoria (mongomock)."""
    return get_client()[get_settings().mongo_db_name]


def as_utc(value: datetime | None) -> datetime | None:
    """Mongo guarda fechas en UTC; según el driver pueden volver sin zona horaria.
    Normalizamos siempre a UTC con zona para poder compararlas con utcnow()."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


@lru_cache
def get_motor_client():
    """Cliente único asíncrono de MongoDB con Motor."""
    from motor.motor_asyncio import AsyncIOMotorClient

    return AsyncIOMotorClient(get_settings().mongo_uri)


def get_database():
    """Dependencia de FastAPI: la base de datos asíncrona de MongoDB (Motor)."""
    return get_motor_client()[get_settings().mongo_db_name]
