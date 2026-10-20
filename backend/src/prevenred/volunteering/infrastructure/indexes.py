"""Índices de voluntarios, incluido el 2dsphere de location."""
from pymongo.database import Database

from prevenred.shared.infrastructure.mongo import ensure_index
from prevenred.volunteering.infrastructure.mongo_volunteer_repository import COLLECTION


def ensure_indexes(db: Database) -> None:
    """Un perfil por cuenta y búsqueda por cercanía. Es idempotente."""
    ensure_index(db[COLLECTION], "userId", name="uq_volunteers_user", unique=True)
    ensure_index(
        db[COLLECTION],
        [("location", "2dsphere")],
        name="ix_volunteers_location_2dsphere",
    )
