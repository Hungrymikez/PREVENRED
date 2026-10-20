"""Índices de técnicos."""
from pymongo.database import Database

from prevenred.services.infrastructure.mongo_technician_repository import COLLECTION
from prevenred.shared.infrastructure.mongo import ensure_index


def ensure_indexes(db: Database) -> None:
    """Un perfil por cuenta. Es idempotente."""
    ensure_index(db[COLLECTION], "userId", name="uq_technicians_user", unique=True)
