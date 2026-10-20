"""
Pruebas de punta a punta del multirrol: la API guarda todos los roles y `require_roles`
deja pasar si la cuenta tiene ALGUNO de los permitidos (RF-03).
"""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.domain.role import Role
from prevenred.identity.interface.dependencies import (
    get_current_token,
    get_token_service,
    require_roles,
)
from prevenred.shared.interface.error_handlers import register_error_handlers

BODY = {
    "full_name": "Camila Pérez", "email": "camila@mail.com", "password": "clave-segura-1",
    "roles": ["CIUDADANO", "TECNICO"], "neighborhood": "Cuba", "accepted_terms": True,
}


def test_la_api_guarda_y_devuelve_todos_los_roles(client):
    r = client.post("/api/v1/auth/register", json=BODY)
    assert r.status_code == 201
    body = r.json()
    assert body["roles"] == ["TECNICO", "CIUDADANO"]   # de mayor a menor privilegio
    assert body["role"] == "TECNICO"                    # el efectivo, sin cambios

    token = client.post(
        "/api/v1/auth/login", json={"email": BODY["email"], "password": BODY["password"]}
    ).json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["roles"] == ["TECNICO", "CIUDADANO"]


def test_el_token_lleva_todos_los_roles(client):
    client.post("/api/v1/auth/register", json=BODY)
    token = client.post(
        "/api/v1/auth/login", json={"email": BODY["email"], "password": BODY["password"]}
    ).json()["access_token"]

    payload = get_token_service().decode(token)
    assert set(payload.roles) == {Role.CIUDADANO, Role.TECNICO}
    assert payload.role is Role.TECNICO


# ---- require_roles: basta con tener uno ----
@pytest.fixture
def app_con_rutas_protegidas() -> FastAPI:
    """App mínima con dos rutas: una de Técnico y una de Administrador."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/tecnico", dependencies=[Depends(require_roles(Role.TECNICO))])
    def tecnico() -> dict:
        return {"ok": True}

    @app.get("/voluntario", dependencies=[Depends(require_roles(Role.VOLUNTARIO))])
    def voluntario() -> dict:
        return {"ok": True}

    @app.get("/admin", dependencies=[Depends(require_roles(Role.ADMINISTRADOR))])
    def admin() -> dict:
        return {"ok": True}
    return app


def _como(app: FastAPI, *roles: Role) -> TestClient:
    """Cliente que entra como la cuenta con esos roles (sin pasar por login)."""
    app.dependency_overrides[get_current_token] = lambda: TokenPayload(
        user_id="a" * 24, roles=roles
    )
    return TestClient(app)


def test_require_roles_acepta_si_tiene_alguno_de_los_roles(app_con_rutas_protegidas):
    client = _como(app_con_rutas_protegidas, Role.CIUDADANO, Role.TECNICO)
    assert client.get("/tecnico").status_code == 200       # tiene Técnico
    assert client.get("/voluntario").status_code == 403   # no tiene Voluntario
    assert client.get("/admin").status_code == 403


def test_require_roles_acepta_cualquier_rol_de_la_cuenta(app_con_rutas_protegidas):
    client = _como(app_con_rutas_protegidas, Role.VOLUNTARIO, Role.TECNICO)
    assert client.get("/tecnico").status_code == 200
    assert client.get("/voluntario").status_code == 200


def test_require_roles_sigue_bloqueando_al_ciudadano(app_con_rutas_protegidas):
    client = _como(app_con_rutas_protegidas, Role.CIUDADANO)
    assert client.get("/tecnico").status_code == 403
