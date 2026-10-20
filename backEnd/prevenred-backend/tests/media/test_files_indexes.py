"""
Pruebas de los índices de `media` (colección `files`).

Antes `files` no tenía `indexes.py`: cada listado recorría la colección completa.
Aquí se comprueba que los tres índices de docs/db/files.md existen tras el arranque
y que cubren las consultas que el repositorio hace de verdad.
"""
from prevenred.media.infrastructure.indexes import ensure_indexes

#: Nombre del índice -> pares (campo, dirección) en el orden en que se consultan.
ESPERADOS = {
    "ix_files_owner_created": [("ownerId", 1), ("createdAt", -1)],
    "ix_files_linked_to": [("linkedTo.id", 1)],
    "ix_files_retention": [("retentionUntil", 1)],
}


def _pares(clave) -> list[tuple[str, int]]:
    """`list_indexes()` devuelve `key` como dict (mongomock) o SON (Mongo real)."""
    if isinstance(clave, dict):
        return list(clave.items())
    return [tuple(par) for par in clave]


def _indices(db) -> dict[str, list[tuple[str, int]]]:
    return {info["name"]: _pares(info["key"]) for info in db["files"].list_indexes()}


def test_el_arranque_crea_los_indices_de_files(db):
    """`db` ya pasó por INDEX_INITIALIZERS (main.py), que incluye media."""
    indices = _indices(db)
    for nombre, clave in ESPERADOS.items():
        assert indices[nombre] == clave


def test_ensure_indexes_se_puede_repetir(db):  # idempotente, como en el lifespan
    ensure_indexes(db)
    ensure_indexes(db)
    assert set(ESPERADOS) <= set(_indices(db))


def test_los_campos_consultados_por_el_repositorio_estan_indexados(db):
    """Las tres consultas de MongoFileRepository empiezan (o filtran) por un campo indexado."""
    indexados = {campo for pares in _indices(db).values() for campo, _ in pares}
    assert {"ownerId", "linkedTo.id", "retentionUntil"} <= indexados


def test_no_se_borran_los_archivos_por_ttl(db):
    """`retentionUntil` NO es TTL: el binario vive en S3 y se borra con código (RN-06)."""
    for info in db["files"].list_indexes():
        assert "expireAfterSeconds" not in info
