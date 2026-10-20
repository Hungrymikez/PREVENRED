"""Índices de notifications. Se crean al arrancar la app (idempotente)."""
from pymongo.database import Database


def ensure_indexes(db: Database) -> None:
    """Crea los índices de la colección `notifications` (CU-06, CU-07)."""
    notices = db["notifications"]
    # Campanita: avisos de la persona, los más recientes primero.
    notices.create_index([("userId", 1), ("createdAt", -1)], name="ix_notifications_user_created")
    # No leídos (CU-07).
    notices.create_index([("userId", 1), ("readAt", 1)], name="ix_notifications_user_read")
    # Reintentos: cola de pendientes por antigüedad.
    notices.create_index([("status", 1), ("createdAt", 1)], name="ix_notifications_status_created")
