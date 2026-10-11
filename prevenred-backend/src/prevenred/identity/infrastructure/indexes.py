"""
Índices de las colecciones de identity. Se crean al arrancar la app (idempotente).
En MongoDB la unicidad del correo la garantiza el ÍNDICE, no solo el código.
"""
from pymongo.database import Database


def ensure_indexes(db: Database) -> None:
    """Crea los índices de la colección users si no existen (se puede ejecutar muchas veces)."""
    db["users"].create_index("email", unique=True, name="uq_users_email")
    db["users"].create_index("status", name="ix_users_status")
