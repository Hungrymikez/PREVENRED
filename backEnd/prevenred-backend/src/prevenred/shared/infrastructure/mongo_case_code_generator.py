"""
Generador de códigos de caso sobre MongoDB: colección `counters` (docs/db/counters.md).

Cómo garantiza que dos casos no repitan número: NO se calcula `count` ni se lee
y luego se escribe (dos peticiones simultáneas leerían el mismo valor). Se usa
`find_one_and_update` con `$inc` y `upsert=True`, que es una sola operación
atómica en el servidor: Mongo devuelve, con `ReturnDocument.AFTER`, el valor YA
incrementado de quien ganó la carrera.

Un contador por tipo de caso y por año (`caseId-INC-2026`): el `_id` es el nombre
del contador, como indica el documento de la colección, y el número vuelve a
empezar en 0001 cada año sin borrar nada.
"""
from pymongo import ReturnDocument
from pymongo.database import Database

from prevenred.shared.application.case_code_generator import CaseCodeGenerator, CaseKind
from prevenred.shared.domain.events import utcnow

COLLECTION = "counters"
#: Ancho del consecutivo: 4 dígitos (`0001`), y crece solo si se pasa de 9999.
CODE_WIDTH = 4


def counter_key(kind: CaseKind, year: int) -> str:
    """Nombre del contador: `caseId-INC-2026` (uno por tipo de caso y año)."""
    return f"caseId-{kind.value}-{year}"


def format_code(kind: CaseKind, year: int, sequence: int) -> str:
    """Arma el código visible: `INC-2026-0001`."""
    return f"{kind.value}-{year}-{sequence:0{CODE_WIDTH}d}"


class MongoCaseCodeGenerator(CaseCodeGenerator):
    """Implementación del puerto sobre la colección `counters`."""

    def __init__(self, db: Database) -> None:
        self._counters = db[COLLECTION]

    def next_code(self, kind: CaseKind, *, year: int | None = None) -> str:
        """Incrementa el contador de (tipo, año) y devuelve el código resultante."""
        target_year = utcnow().year if year is None else year
        # `$inc` + `upsert` en UNA operación: el incremento ocurre en el servidor y
        # nadie puede quedarse con el mismo número. `$setOnInsert` solo se aplica
        # la primera vez y deja constancia de qué contador es.
        document = self._counters.find_one_and_update(
            {"_id": counter_key(kind, target_year)},
            {
                "$inc": {"seq": 1},
                "$setOnInsert": {"kind": kind.value, "year": target_year},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return format_code(kind, target_year, int(document["seq"]))
