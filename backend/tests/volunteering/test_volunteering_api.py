"""Caja blanca de voluntariado: registro, asignación (403/404) y misiones propias."""

import pytest

from prevenred.auth.domain.role import Role
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId
from prevenred.volunteering.domain.volunteer import VolunteerAssignment

BASE = "/api/v1/volunteering"
INCIDENT_ID = "64b7f0c2a1b2c3d4e5f60718"


def _register(api, **overrides):
    body = {
        "full_name": "Laura Rescatista",
        "phone_number": "3101234567",
        "skills": ["RESCATE"],
        "longitude": -75.69,
        "latitude": 4.81,
        **overrides,
    }
    return api.post(f"{BASE}/register", json=body)


def _assign(api, volunteer_id, task="Evacuar familias del sector"):
    return api.post(
        f"{BASE}/assign",
        json={"volunteer_id": volunteer_id, "incident_id": INCIDENT_ID, "task_description": task},
    )


def test_registro_y_re_registro_reutilizan_el_perfil(api, act_as, make_user, motor_db):
    user = act_as(make_user())
    first = _register(api)
    second = _register(api, skills=["LOGISTICA"])

    assert first.status_code == second.status_code == 201
    assert first.json()["user_id"] == user.id
    assert first.json()["is_available"] is True
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["skills"] == ["LOGISTICA"]
    assert motor_db["volunteers"]._col.count_documents({}) == 1


@pytest.mark.parametrize("role", [Role.CIUDADANO, Role.TECNICO])
def test_asignar_sin_rol_coordinador_responde_403(api, act_as, make_user, role):
    act_as(make_user())
    vol_id = _register(api).json()["id"]
    act_as(make_user(role))
    assert _assign(api, vol_id).status_code == 403


def test_asignar_voluntario_inexistente_responde_404(api, act_as, make_user):
    act_as(make_user(Role.ADMIN))
    assert _assign(api, "64b7f0c2a1b2c3d4e5f60799").status_code == 404


@pytest.mark.parametrize("role", [Role.ADMIN, Role.INSPECTOR])
def test_coordinador_asigna_y_el_voluntario_ve_su_mision(api, act_as, make_user, role):
    volunteer = act_as(make_user())
    vol_id = _register(api).json()["id"]
    coordinator = act_as(make_user(role))

    r = _assign(api, vol_id)
    assert r.status_code == 201
    assert r.json()["assigned_by"] == coordinator.id
    assert r.json()["status"] == "ASIGNADO"

    act_as(volunteer)
    [mission] = api.get(f"{BASE}/assignments/my").json()
    assert mission["id"] == r.json()["id"]
    assert mission["incident_id"] == INCIDENT_ID


def test_mis_misiones_de_quien_no_es_voluntario_es_lista_vacia(api, act_as, make_user):
    act_as(make_user())
    r = api.get(f"{BASE}/assignments/my")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.parametrize(("lon", "lat", "status"), [(180, 90, 201), (180.01, 0, 422)])
def test_limites_de_coordenadas(api, act_as, make_user, lon, lat, status):
    act_as(make_user())
    assert _register(api, longitude=lon, latitude=lat).status_code == status


@pytest.mark.parametrize("task", ["", "    ", "abcd", " abcd "])
def test_descripcion_de_tarea_menor_a_5_caracteres_es_invalida(task):
    with pytest.raises(DomainValidationError):
        VolunteerAssignment.create(
            volunteer_id=EntityId.generate(),
            incident_id=EntityId.generate(),
            task_description=task,
            assigned_by=EntityId.generate(),
        )


def test_descripcion_de_exactamente_5_caracteres_es_valida():
    assignment = VolunteerAssignment.create(
        volunteer_id=EntityId.generate(),
        incident_id=EntityId.generate(),
        task_description=" abcde ",
        assigned_by=EntityId.generate(),
    )
    assert assignment.task_description == "abcde"
