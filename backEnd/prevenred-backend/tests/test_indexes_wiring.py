"""
Conformidad del arranque: los índices se definen en UN solo lugar (`main.py`) y las
pruebas usan esa misma lista.

Por qué: `INDEX_INITIALIZERS` estaba duplicado en `main.py` (lifespan real) y en
`tests/conftest.py` (Mongo en memoria). Si alguien agregaba un contexto a uno solo,
las pruebas podían pasar con colecciones sin sus índices únicos o, al revés, la
base real arrancar sin ellos. Hoy `tests/conftest.py` IMPORTA la lista de `main.py`,
y este test lo verifica.
"""
from fastapi.testclient import TestClient

from prevenred import main
from tests.conftest import INDEX_INITIALIZERS as TEST_INITIALIZERS


def test_las_pruebas_usan_la_misma_lista_de_indices_que_main():
    assert TEST_INITIALIZERS is main.INDEX_INITIALIZERS, (
        "tests/conftest.py debe importar INDEX_INITIALIZERS de main.py, no copiarla."
    )


def test_cada_contexto_con_colecciones_aporta_sus_indices():
    contexts = {fn.__module__.split(".")[1] for fn in main.INDEX_INITIALIZERS}
    assert contexts == {
        "identity", "marketplace", "services", "wellbeing", "fieldwork",
        "incidents", "geo", "aid", "media", "notifications", "shared",
    }


def test_cada_inicializador_aparece_una_sola_vez():
    """Dos veces la misma función no rompe nada (es idempotente), pero es un error."""
    modules = [fn.__module__ for fn in main.INDEX_INITIALIZERS]
    assert len(modules) == len(set(modules))


def test_el_lifespan_recorre_los_inicializadores(monkeypatch):
    """El arranque ejecuta cada inicializador: aquí se registra la llamada, sin base real."""
    called: list[str] = []

    def fake_indexes(_db=None) -> None:
        called.append("ok")

    monkeypatch.setattr(main, "INDEX_INITIALIZERS", [fake_indexes] * 3)
    with TestClient(main.create_app()) as client:   # 'with' sí ejecuta el lifespan
        assert client.get("/openapi.json").status_code == 200
    assert len(called) == 3
