"""
Índices de las colecciones de identity. Se crean al arrancar la app (idempotente).
En MongoDB la unicidad del correo la garantiza el ÍNDICE, no solo el código.
"""

from pymongo.database import Database

from prevenred.shared.infrastructure.mongo import ensure_index


def ensure_indexes(db: Database) -> None:
    """Crea los índices de la colección users si no existen (se puede ejecutar muchas veces)."""
    ensure_index(db["users"], "email", name="uq_users_email", unique=True)
    ensure_index(db["users"], "status", name="ix_users_status")
