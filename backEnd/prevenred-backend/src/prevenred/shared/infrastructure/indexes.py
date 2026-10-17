"""
Índices de las colecciones de shared. Se crean al arrancar la app (idempotente).

`counters` (RF-22) no necesita índices propios: se busca siempre por `_id`, que ya
está indexado.

`service_requests` todavía no tiene código (docs/EQUIVALENCIAS_BD.md, fila 12:
"Pendiente", con `caseId` `SRV-AAAA-0001`). Se le deja aquí el índice único del
consecutivo para que no pueda nacer sin esa garantía. Es PARCIAL (`$type: string`):
los documentos sin `caseId` no participan y no chocan entre sí por un valor nulo.

Las colecciones que ya tienen código (`incidents`, `properties`, `aidNeeds`) definen
su propio `uq_*_case` en su contexto, con su nombre y sus opciones: no se repiten
aquí, porque dos índices distintos sobre el mismo campo harían fallar el arranque.
"""
from pymongo.database import Database

#: Colecciones con consecutivo que AÚN no tienen módulo de índices propio.
PENDING_CASE_COLLECTIONS = ("service_requests",)


def ensure_indexes(db: Database) -> None:
    """Crea los índices que le corresponden a shared."""
    for collection in PENDING_CASE_COLLECTIONS:
        db[collection].create_index(
            "caseId",
            unique=True,
            name=f"uq_{collection}_case",
            partialFilterExpression={"caseId": {"$type": "string"}},
        )

