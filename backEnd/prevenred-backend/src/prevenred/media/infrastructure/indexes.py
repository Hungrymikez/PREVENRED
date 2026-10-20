"""
Índices de las colecciones de media. Se crean al arrancar la app (idempotente).

`files` no tenía índices: cada consulta recorría la colección completa. Según
docs/db/files.md se indexa:
  - `ownerId` + `createdAt`: "mis archivos, el más reciente primero".
  - `linkedTo.id`: las evidencias de un reporte o de una inspección.
  - `retentionUntil`: la revisión periódica de RN-06 (qué archivos ya vencieron).
    Es índice normal, NO TTL: el binario vive en S3/MinIO y hay que borrarlo con
    código; si Mongo borrara el documento solo, la referencia se perdería y el
    binario quedaría huérfano.
"""
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database


def ensure_indexes(db: Database) -> None:
    """Crea los índices de `files` si no existen (se puede repetir)."""
    files = db["files"]
    files.create_index(
        [("ownerId", ASCENDING), ("createdAt", DESCENDING)],
        name="ix_files_owner_created",
    )
    files.create_index("linkedTo.id", name="ix_files_linked_to")
    files.create_index("retentionUntil", name="ix_files_retention")
