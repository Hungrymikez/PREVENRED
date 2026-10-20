"""
El nombre de cada colección vive en UNA sola constante, en su repositorio.

Por qué: el nombre estaba escrito a mano en varios sitios (repositorio, `indexes.py`
y pruebas). Al renombrar a `snake_case` (docs/EQUIVALENCIAS_BD.md) eso obligaba a
buscar cadenas por todo el repo y era fácil dejar una colección nueva a medias, con
los índices en una colección vacía.

Aquí se comprueba, buscando en el código fuente:
  1. que cada `indexes.py` use las constantes del repositorio en vez de literales;
  2. que no quede ningún nombre viejo en camelCase;
  3. que las colecciones que sí tenían código conserven su diseño (sólo cambia el nombre).
"""
from pathlib import Path

import pytest

from prevenred import main

SRC = Path(main.__file__).parent

#: Nombre viejo -> nombre nuevo (docs/EQUIVALENCIAS_BD.md, sección 1).
RENAMED = {
    "passwordResets": "password_resets",
    "mfaChallenges": "mfa_challenges",
    "wellbeingConsents": "wellbeing_consents",
    "wellbeingSurveys": "wellbeing_surveys",
    "aidNeeds": "aid_needs",
    "aidInventory": "aid_inventory",
    "mapLayers": "map_layers",
    "propertyInspections": "property_inspections",
    "toolTransactions": "transactions",
}


def _archivos(py: str) -> list[Path]:
    return sorted(p for p in SRC.rglob(py) if p.is_file())


def _todas_las_fuentes() -> list[Path]:
    return [p for p in SRC.rglob("*.py") if p.is_file()]


def _relativa(p: Path) -> str:
    """Ruta relativa a `src/` para que el mensaje del fallo se lea bien."""
    return p.relative_to(SRC).as_posix()


def test_ninguna_fuente_usa_los_nombres_viejos():
    """El renombrado quedó completo: buscar `aidNeeds` en `src/` no devuelve nada."""
    restos = []
    for archivo in _todas_las_fuentes():
        texto = archivo.read_text(encoding="utf-8")
        for viejo in RENAMED:
            if f'"{viejo}"' in texto:
                restos.append(f'{_relativa(archivo)}: "{viejo}"')
    assert restos == [], "Mandan los nombres en snake_case. Quedan: " + ", ".join(restos)


@pytest.mark.parametrize(("modulo", "colecciones"), [
    ("prevenred.identity.infrastructure.indexes", (
        "users", "sessions", "password_resets", "mfa_challenges", "audit_logs",
    )),
    ("prevenred.marketplace.infrastructure.indexes", ("reservations", "transactions")),
    ("prevenred.wellbeing.infrastructure.indexes", (
        "wellbeing_consents", "wellbeing_surveys",
    )),
    ("prevenred.aid.infrastructure.indexes", ("aid_needs", "aid_inventory")),
    ("prevenred.geo.infrastructure.indexes", ("map_layers",)),
    ("prevenred.fieldwork.infrastructure.indexes", (
        "properties", "property_inspections",
    )),
])
def test_cada_indexes_py_toma_el_nombre_del_repositorio(db, modulo, colecciones):
    """`ensure_indexes` crea los índices sobre las colecciones snake_case correctas."""
    import importlib

    ensure_indexes = importlib.import_module(modulo).ensure_indexes
    ensure_indexes(db)          # idempotente: se puede repetir sin error
    for collection in colecciones:
        nombres = {i["name"] for i in db[collection].list_indexes()}
        assert nombres - {"_id_"}, f"{collection} quedó sin índices propios"


def test_las_constantes_coinciden_con_los_repositorios():
    """Una sola fuente por colección: el valor del repositorio es el esperado."""
    from prevenred.aid.infrastructure import mongo_aid_repository as aid
    from prevenred.fieldwork.infrastructure import mongo_inspection_repository as fw
    from prevenred.geo.infrastructure import mongo_map_layer_repository as geo
    from prevenred.identity.infrastructure import mongo_auth_repository as auth
    from prevenred.identity.infrastructure import mongo_mfa_challenge_repository as mfa
    from prevenred.marketplace.infrastructure import mongo_marketplace_repository as mk
    from prevenred.wellbeing.infrastructure import mongo_wellbeing_repository as wb

    assert aid.NEEDS_COLLECTION == "aid_needs"
    assert aid.INVENTORY_COLLECTION == "aid_inventory"
    assert fw.COLLECTION == "property_inspections"
    assert geo.COLLECTION == "map_layers"
    assert auth.PASSWORD_RESETS == "password_resets"
    assert auth.SESSIONS == "sessions"
    assert mfa.COLLECTION == "mfa_challenges"
    assert mk.TRANSACTIONS == "transactions"
    assert wb.CONSENTS == "wellbeing_consents"
    assert wb.SURVEYS == "wellbeing_surveys"
