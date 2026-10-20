"""Caja blanca de OficiosYa: registro/actualización, verificación (403/404) y búsqueda."""

import pytest

from prevenred.identity.domain.role import Role
from prevenred.services.domain.technician import Specialty, TechnicianProfile
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId

BASE = "/api/v1/services/technicians"
ORIGIN = (-75.6961, 4.8143)


def _register(api, **overrides):
    body = {
        "full_name": "Carlos Plomero",
        "phone_number": "+57 310 123 4567",
        "specialties": ["PLOMERIA"],
        "experience_years": 5,
        "bio": "  Reparaciones  ",
        "longitude": ORIGIN[0],
        "latitude": ORIGIN[1],
        **overrides,
    }
    return api.post(f"{BASE}/profile", json=body)


def _search(api, **params):
    return api.get(
        f"{BASE}/search", params={"longitude": ORIGIN[0], "latitude": ORIGIN[1], **params}
    )


def test_registro_normaliza_telefono_y_queda_pendiente(api, act_as, make_user):
    user = act_as(make_user(Role.TECNICO))
    r = _register(api)
    assert r.status_code == 201
    body = r.json()
    assert body["user_id"] == user.id
    assert body["phone_number"] == "+573101234567"
    assert body["bio"] == "Reparaciones"
    assert body["verification_status"] == "PENDIENTE"


def test_re_registro_actualiza_el_mismo_perfil(api, act_as, make_user, motor_db):
    act_as(make_user(Role.TECNICO))
    first = _register(api).json()
    second = _register(api, full_name="Carlos Electricista", specialties=["ELECTRICIDAD"]).json()

    assert second["id"] == first["id"]
    assert second["specialties"] == ["ELECTRICIDAD"]
    assert motor_db["technicians"]._col.count_documents({}) == 1


def test_verificar_por_no_admin_responde_403(api, act_as, make_user):
    act_as(make_user(Role.TECNICO))
    tech_id = _register(api).json()["id"]
    act_as(make_user(Role.INSPECTOR))
    r = api.patch(f"{BASE}/{tech_id}/verify", json={"approve": True})
    assert r.status_code == 403


def test_verificar_tecnico_inexistente_responde_404(api, act_as, make_user):
    act_as(make_user(Role.ADMIN))
    r = api.patch(f"{BASE}/64b7f0c2a1b2c3d4e5f60718/verify", json={"approve": True})
    assert r.status_code == 404


@pytest.mark.parametrize(("approve", "expected"), [(True, "VERIFICADO"), (False, "RECHAZADO")])
def test_admin_aprueba_o_rechaza(api, act_as, make_user, motor_db, approve, expected):
    act_as(make_user(Role.TECNICO))
    tech_id = _register(api).json()["id"]
    admin = act_as(make_user(Role.ADMIN))

    r = api.patch(f"{BASE}/{tech_id}/verify", json={"approve": approve})
    assert r.status_code == 200
    assert r.json()["verification_status"] == expected
    assert motor_db["technicians"]._col.find_one({"_id": tech_id})["verified_by"] == admin.id


def test_busqueda_respeta_only_verified_y_especialidad(api, act_as, make_user):
    act_as(make_user(Role.TECNICO))
    pendiente = _register(api).json()
    act_as(make_user(Role.TECNICO))
    verificado = _register(api, specialties=["ELECTRICIDAD", "PLOMERIA"]).json()
    act_as(make_user(Role.ADMIN))
    api.patch(f"{BASE}/{verificado['id']}/verify", json={"approve": True})

    assert [t["id"] for t in _search(api).json()] == [verificado["id"]]
    todos = {t["id"] for t in _search(api, only_verified=False).json()}
    assert todos == {pendiente["id"], verificado["id"]}
    assert _search(api, specialty="CARPINTERIA", only_verified=False).json() == []


@pytest.mark.parametrize(
    ("params", "status"),
    [({"radius_meters": 99}, 422), ({"radius_meters": 50001}, 422), ({"limit": 101}, 422)],
)
def test_limites_de_busqueda(api, params, status):
    assert _search(api, **params).status_code == status


def test_enlace_whatsapp(api, act_as, make_user):
    act_as(make_user(Role.TECNICO))
    tech_id = _register(api).json()["id"]

    r = api.get(f"{BASE}/{tech_id}/whatsapp", params={"message": "Hola!"})
    assert r.status_code == 200
    assert r.json() == {
        "technician_name": "Carlos Plomero",
        "whatsapp_url": "https://wa.me/573101234567?text=Hola%21",
    }
    assert api.get(f"{BASE}/64b7f0c2a1b2c3d4e5f60718/whatsapp").status_code == 404


def test_whatsapp_con_mensaje_vacio_usa_saludo_por_defecto():
    profile = TechnicianProfile.create(
        user_id=EntityId.generate(),
        full_name="Ana",
        phone_number="3101234567",
        specialties=[Specialty.PINTURA],
        experience_years=0,
        bio="",
        longitude=0,
        latitude=0,
    )
    assert "Hola%20Ana" in profile.generate_whatsapp_link(message="   ")


@pytest.mark.parametrize(
    "overrides",
    [
        {"full_name": "Al"},
        {"phone_number": "12-34"},
        {"specialties": []},
        {"experience_years": -1},
        {"longitude": 180.5},
        {"latitude": -90.5},
    ],
)
def test_guard_clauses_del_perfil_tecnico(overrides):
    data = {
        "user_id": EntityId.generate(),
        "full_name": "Ana María",
        "phone_number": "3101234567",
        "specialties": [Specialty.PLOMERIA],
        "experience_years": 1,
        "bio": "",
        "longitude": 0.0,
        "latitude": 0.0,
        **overrides,
    }
    with pytest.raises(DomainValidationError):
        TechnicianProfile.create(**data)
