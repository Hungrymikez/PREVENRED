"""
Pruebas del consecutivo de casos (RF-22) contra Mongo en memoria.

Lo que se comprueba: el formato (`INC-2026-0001`), que dos llamadas NUNCA repiten
número, que cada tipo de caso lleva su propio contador y que el número vuelve a
empezar cada año sin borrar nada.
"""
import pytest

from prevenred.shared.application.case_code_generator import CaseKind
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.mongo_case_code_generator import (
    MongoCaseCodeGenerator,
    counter_key,
)


@pytest.fixture
def generator(db) -> MongoCaseCodeGenerator:
    return MongoCaseCodeGenerator(db)


def test_el_formato_es_tipo_ano_y_cuatro_digitos(generator):
    assert generator.next_code(CaseKind.INCIDENTE, year=2026) == "INC-2026-0001"


def test_dos_llamadas_nunca_repiten_numero(generator):
    """La prueba central: el garantía es del $inc atómico, no del código llamador."""
    year = utcnow().year
    first = generator.next_code(CaseKind.INCIDENTE)
    second = generator.next_code(CaseKind.INCIDENTE)
    assert first != second
    assert (first, second) == (f"INC-{year}-0001", f"INC-{year}-0002")


def test_muchas_llamadas_no_repiten_ningun_codigo(generator):  # RF-22
    codes = [generator.next_code(CaseKind.AYUDA) for _ in range(50)]
    assert len(set(codes)) == 50
    assert codes[-1].endswith("-0050")


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (CaseKind.INCIDENTE, "INC-2026-0001"),
        (CaseKind.INMUEBLE, "INM-2026-0001"),
        (CaseKind.AYUDA, "AYU-2026-0001"),
        (CaseKind.SERVICIO, "SRV-2026-0001"),
    ],
)
def test_cada_tipo_de_caso_lleva_su_propio_consecutivo(generator, kind, expected):
    assert generator.next_code(kind, year=2026) == expected


def test_cada_ano_empieza_de_nuevo_sin_borrar_el_anterior(generator, db):
    generator.next_code(CaseKind.INMUEBLE, year=2025)
    generator.next_code(CaseKind.INMUEBLE, year=2025)
    assert generator.next_code(CaseKind.INMUEBLE, year=2026) == "INM-2026-0001"
    assert db["counters"].find_one({"_id": counter_key(CaseKind.INMUEBLE, 2025)})["seq"] == 2


def test_el_contador_se_guarda_con_el_diseno_de_counters_md(generator, db):
    generator.next_code(CaseKind.INCIDENTE, year=2026)
    doc = db["counters"].find_one({"_id": "caseId-INC-2026"})
    assert doc["seq"] == 1 and doc["kind"] == "INC" and doc["year"] == 2026


def test_un_segundo_generador_continua_el_consecutivo(db):
    """Dos procesos con su propio generador NO repiten: comparten el documento."""
    assert MongoCaseCodeGenerator(db).next_code(CaseKind.SERVICIO, year=2026) == "SRV-2026-0001"
    assert MongoCaseCodeGenerator(db).next_code(CaseKind.SERVICIO, year=2026) == "SRV-2026-0002"
