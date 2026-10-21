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
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure

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


def ensure_index(
    collection: Collection,
    keys: str | list,
    *,
    name: str,
    unique: bool = False,
) -> None:
    """Crea el índice si no hay otro con las mismas claves y la misma unicidad.

    Atlas a veces ya trae el índice con el nombre por defecto (`email_1`).
    Volver a crearlo con otro nombre rompe el arranque (IndexOptionsConflict).
    """
    spec = _index_keys(keys)
    for existing_name, info in collection.index_information().items():
        if existing_name == "_id_":
            continue
        same_keys = _index_keys(info.get("key") or []) == spec
        if same_keys and bool(info.get("unique")) == unique:
            return
    try:
        collection.create_index(spec, name=name, unique=unique)
    except OperationFailure as exc:
        if exc.code != 85:
            raise


def _index_keys(keys: str | list) -> list[tuple]:
    if isinstance(keys, str):
        return [(keys, 1)]
    return [(field, direction) for field, direction in keys]


@lru_cache
def get_motor_client():
    """Cliente único asíncrono de MongoDB con Motor."""
    from motor.motor_asyncio import AsyncIOMotorClient

    return AsyncIOMotorClient(get_settings().mongo_uri)


def get_database():
    """Dependencia de FastAPI: la base de datos asíncrona de MongoDB (Motor)."""
    return get_motor_client()[get_settings().mongo_db_name]
