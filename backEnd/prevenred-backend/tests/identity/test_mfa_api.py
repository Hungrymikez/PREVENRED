"""
Pruebas de punta a punta del segundo factor (CU-03) y de la gestión de cuentas
administrativas (CU-08) sobre la API, con MongoDB en memoria.

Flujo que se comprueba (el real, con tokens de verdad):

  POST /auth/login         Administrador -> 200, mfa_required, token "challenge"
  POST /auth/mfa/request   -> entrega el código del desafío
  POST /auth/mfa/verify    -> valida el código y devuelve el token de sesión "bearer"
  POST /auth/users         -> crea la cuenta de Inspector/Administrador

El registro público NO crea Administradores (CU-01), así que la cuenta
administrativa se siembra en la base, como la primera cuenta de la entidad.
"""
import pytest
from bson import ObjectId

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.identity.infrastructure.mongo_mfa_challenge_repository import (
    COLLECTION as CHALLENGES,
)
from prevenred.identity.infrastructure.mongo_user_repository import (
    COLLECTION as USERS,
)
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.identity.infrastructure.second_factor_gateway import (
    InMemorySecondFactorGateway,
)
from prevenred.identity.interface.dependencies import get_second_factor_gateway

ADMIN = {"email": "admin@prevenred.gov.co", "password": "clave-admin-1"}
LOGIN = "login"                 # operación del propio inicio de sesión (CU-02 A1)
ADMIN_USERS = "admin_users"     # operación del segundo factor de CU-08

NEW_ACCOUNT = {
    "full_name": "Iván Inspector", "email": "ivan@prevenred.gov.co",
    "role": "INSPECTOR", "neighborhood": "Cuba",
}

#: Gateway que usa la API en estas pruebas. El de v1 guarda en memoria el código
#: entregado de cada secreto: así la prueba puede "recibirlo" aunque todavía no
#: exista un canal de envío real (doc 07, O-16).
GATEWAY = InMemorySecondFactorGateway()


@pytest.fixture
def segundo_factor(client):
    """Fuerza que la API use el gateway de la prueba (sin depender del orden)."""
    client.app.dependency_overrides[get_second_factor_gateway] = lambda: GATEWAY
    yield GATEWAY
    client.app.dependency_overrides.pop(get_second_factor_gateway, None)


@pytest.fixture
def admin(db) -> User:
    """Cuenta administrativa activa sembrada directamente en la base."""
    return _seed(db, **ADMIN)


def _seed(
    db, *, email: str, password: str, role: Role = Role.ADMINISTRADOR,
    active: bool = True,
) -> User:
    """Crea una cuenta directamente en la base (sin pasar por los endpoints)."""
    user = User.open_administratively(
        full_name="Ana Administradora", email=Email(email),
        password_hash=Argon2PasswordHasher().hash(password),
        roles=role, neighborhood="Centro",
        privacy_notice_version="v1", created_by="siembra",
    )
    user.pull_events()                     # la siembra no publica eventos
    if not active:
        user.suspend()
        user.pull_events()
    MongoUserRepository(db).add(user)
    return user


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _codigo(secret_enc: str) -> str:
    """Código vigente de ese secreto (v1 no tiene canal de envío: se lee del gateway)."""
    digest = GATEWAY._current[secret_enc]      # noqa: SLF001 - es el doble de prueba
    return GATEWAY._issued[digest]             # noqa: SLF001 - es el doble de prueba


def _secreto(db, user_id: str) -> str:
    """Secreto del segundo factor CIFRADO, tal como quedó guardado en la cuenta."""
    doc = db[USERS].find_one({"_id": ObjectId(user_id)}, {"security.mfa.secretEnc": 1})
    return doc["security"]["mfa"]["secretEnc"]


def _login(client, credentials: dict = ADMIN):
    """Login del Administrador: 200, `mfa_required` y token de desafío."""
    return client.post("/api/v1/auth/login", json=credentials)


def _sesion(client, db, user: User) -> str:
    """Recorre el flujo REAL del Administrador y devuelve su token de SESIÓN."""
    login = _login(client, {"email": user.email.value, "password": ADMIN["password"]})
    assert login.status_code == 200, login.text
    assert login.json()["token_type"] == "challenge"
    r = client.post(
        "/api/v1/auth/mfa/verify",
        json={"purpose": LOGIN, "code": _codigo(_secreto(db, user.id))},
        headers=_bearer(login.json()["access_token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["token_type"] == "bearer"
    return r.json()["access_token"]


def _verificar_admin_users(client, db, user: User) -> str:
    """Valida el segundo factor de CU-08 y devuelve el token de sesión vigente."""
    token = _sesion(client, db, user)
    r = client.post(
        "/api/v1/auth/mfa/request", json={"purpose": ADMIN_USERS}, headers=_bearer(token)
    )
    assert r.status_code == 200, r.text
    code = _codigo(_secreto(db, user.id))          # antes de validar: se consume
    r = client.post(
        "/api/v1/auth/mfa/verify",
        json={"purpose": ADMIN_USERS, "code": code},
        headers=_bearer(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["token_type"] is None           # NO abre una sesión nueva
    return token


# --------------------------------------------------------------- CU-02: el bug
def test_login_de_administrador_ya_no_da_500(client, segundo_factor, admin):
    """Antes: 500 (`access_token=None` no cabía en el schema). Ahora: 200 + MFA."""
    r = _login(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mfa_required"] is True
    assert body["token_type"] == "challenge"
    assert body["role"] == "ADMINISTRADOR"
    assert body["access_token"]


def test_login_de_ciudadano_sigue_devolviendo_sesion(client, segundo_factor):
    """La cuenta no administrativa no cambió: recibe su token de sesión directo."""
    body = {
        "full_name": "Camila Pérez", "email": "camila@mail.com",
        "password": "clave-segura-1", "roles": ["CIUDADANO"],
        "neighborhood": "Cuba", "accepted_terms": True,
    }
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    r = client.post(
        "/api/v1/auth/login", json={"email": body["email"], "password": body["password"]}
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer" and r.json()["mfa_required"] is False
    token = r.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=_bearer(token)).status_code == 200


def test_el_login_deja_abierto_el_desafio_del_segundo_factor(client, segundo_factor, admin, db):
    _login(client)
    doc = db[CHALLENGES].find_one({"purpose": LOGIN})
    assert doc is not None
    assert doc["status"] == "PENDIENTE"
    assert doc["secretEnc"]                          # el secreto se guarda cifrado
    assert doc["codeHash"] != doc["secretEnc"]       # el código, solo como hash


def test_el_token_de_desafio_no_abre_la_sesion(client, segundo_factor, admin):
    """El token `challenge` solo sirve para validar el código: no es una sesión."""
    token = _login(client).json()["access_token"]
    r = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_el_token_de_desafio_no_sirve_para_crear_cuentas(client, segundo_factor, admin):
    """Un token `challenge` con rol Administrador tampoco pasa el RBAC de CU-08."""
    token = _login(client).json()["access_token"]
    r = client.post("/api/v1/auth/users", json=NEW_ACCOUNT, headers=_bearer(token))
    assert r.status_code == 401


# ----------------------------------------------------- CU-03: pedir y validar
def test_el_flujo_completo_del_mfa_abre_la_sesion(client, segundo_factor, admin, db):
    """login -> pedir código -> validar: el Administrador termina con sesión real."""
    token = _sesion(client, db, admin)
    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN["email"]
    assert me.json()["role"] == "ADMINISTRADOR"


def test_validar_el_codigo_guarda_la_verificacion_y_limpia_los_fallos(
    client, segundo_factor, admin, db
):
    _sesion(client, db, admin)
    doc = db[CHALLENGES].find_one({"purpose": LOGIN})
    assert doc["status"] == "VERIFICADO" and doc["verifiedAt"] is not None
    guardado = db[USERS].find_one({"_id": ObjectId(admin.id)})
    assert guardado["security"]["failedLoginAttempts"] == 0
    assert guardado["security"]["mfa"]["enabled"] is True


def test_el_codigo_es_de_un_solo_uso(client, segundo_factor, admin, db):
    """CU-03 paso 3: validado una vez, el mismo código ya no sirve."""
    login = _login(client)
    token = login.json()["access_token"]
    code = _codigo(_secreto(db, admin.id))
    headers = _bearer(token)
    assert client.post(
        "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": code}, headers=headers
    ).status_code == 200
    r = client.post(
        "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": code}, headers=headers
    )
    assert r.status_code == 409                     # no hay verificación en curso


def test_un_codigo_incorrecto_da_401_y_no_abre_sesion(client, segundo_factor, admin):
    """CU-03 E1: el código equivocado no autoriza y permite reintentar."""
    token = _login(client).json()["access_token"]
    r = client.post(
        "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": "000000"},
        headers=_bearer(token),
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"
    assert "intento" in r.json()["error"]["message"]


def test_un_codigo_mal_formado_cuenta_como_intento_fallido(client, segundo_factor, admin):
    """E1: se responde 401 (no 422), para no distinguirlo de un código equivocado."""
    token = _login(client).json()["access_token"]
    r = client.post(
        "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": "12"},
        headers=_bearer(token),
    )
    assert r.status_code == 401


def test_agotar_los_intentos_bloquea_la_operacion(client, segundo_factor, admin):
    """CU-03 E2: tras MFA_MAX_ATTEMPTS fallos, todo responde 429."""
    token = _login(client).json()["access_token"]
    codes = [r.status_code for r in (
        client.post(
            "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": "000000"},
            headers=_bearer(token),
        ) for _ in range(3)
    )]
    assert codes == [401, 401, 429]
    # Aun con el código correcto, la operación sigue bloqueada.
    r = client.post(
        "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": "111111"},
        headers=_bearer(token),
    )
    assert r.status_code == 429


def test_validar_sin_token_da_401(client, segundo_factor, admin):
    r = client.post("/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": "000000"})
    assert r.status_code == 401


def test_con_sesion_abierta_no_se_puede_volver_a_validar_el_login(
    client, segundo_factor, admin, db
):
    """`purpose=login` solo lo atiende el token de desafío: con sesión, 401."""
    sesion = _sesion(client, db, admin)
    pedido = client.post(
        "/api/v1/auth/mfa/request", json={"purpose": LOGIN}, headers=_bearer(sesion)
    )
    assert pedido.status_code == 401
    validacion = client.post(
        "/api/v1/auth/mfa/verify", json={"purpose": LOGIN, "code": "123456"},
        headers=_bearer(sesion),
    )
    assert validacion.status_code == 401


def test_pedir_codigo_sin_token_da_401(client, segundo_factor, admin):
    r = client.post("/api/v1/auth/mfa/request", json={"purpose": LOGIN})
    assert r.status_code == 401


def test_pedir_codigo_con_un_desafio_vigente_da_409(client, segundo_factor, admin, db):
    """A1: no se abre un desafío nuevo mientras el anterior sigue vigente."""
    token = _sesion(client, db, admin)
    primera = client.post(
        "/api/v1/auth/mfa/request", json={"purpose": ADMIN_USERS}, headers=_bearer(token)
    )
    segunda = client.post(
        "/api/v1/auth/mfa/request", json={"purpose": ADMIN_USERS}, headers=_bearer(token)
    )
    assert primera.status_code == 200
    assert segunda.status_code == 409
    assert segunda.json()["error"]["code"] == "conflict"


# ------------------------------------------------- CU-08: gestión de cuentas
def test_un_administrador_con_mfa_verificado_crea_una_cuenta(
    client, segundo_factor, admin, db
):
    """CU-08 A1: crea la cuenta y devuelve la contraseña temporal UNA vez."""
    token = _verificar_admin_users(client, db, admin)
    r = client.post("/api/v1/auth/users", json=NEW_ACCOUNT, headers=_bearer(token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == NEW_ACCOUNT["email"]
    assert body["user"]["role"] == "INSPECTOR"
    assert body["user"]["roles"] == ["INSPECTOR"]
    assert len(body["temporary_password"]) >= 8
    # La contraseña temporal NO queda guardada en claro (solo su hash).
    guardado = db[USERS].find_one({"email": NEW_ACCOUNT["email"]})
    assert body["temporary_password"] not in str(guardado)
    # TODO(CU-05): `create_account` aún no escribe en `audit_logs` (solo cambio de
    # rol, suspensión y reactivación lo hacen). Aquí no se exige hasta corregirlo.


def test_tambien_se_puede_crear_otro_administrador(client, segundo_factor, admin, db):
    token = _verificar_admin_users(client, db, admin)
    r = client.post(
        "/api/v1/auth/users", json={**NEW_ACCOUNT, "role": "ADMINISTRADOR"},
        headers=_bearer(token),
    )
    assert r.status_code == 201
    assert r.json()["user"]["roles"] == ["ADMINISTRADOR"]


def test_crear_cuentas_exige_la_verificacion_en_dos_pasos(client, segundo_factor, admin, db):
    """RN-07: con sesión pero sin MFA de `admin_users`, no se puede administrar."""
    token = _sesion(client, db, admin)
    r = client.post("/api/v1/auth/users", json=NEW_ACCOUNT, headers=_bearer(token))
    assert r.status_code == 403
    assert "dos pasos" in r.json()["error"]["message"]


def test_crear_cuentas_sin_token_da_401(client, segundo_factor):
    r = client.post("/api/v1/auth/users", json=NEW_ACCOUNT)
    assert r.status_code == 401


def test_crear_cuentas_con_otro_rol_da_403(client, segundo_factor):
    """RBAC (`require_roles`): un Técnico no entra a la gestión de cuentas."""
    body = {
        "full_name": "Teo Técnico", "email": "teo@mail.com", "password": "clave-segura-1",
        "roles": ["TECNICO"], "neighborhood": "Cuba", "accepted_terms": True,
    }
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    token = client.post(
        "/api/v1/auth/login", json={"email": body["email"], "password": body["password"]}
    ).json()["access_token"]
    r = client.post("/api/v1/auth/users", json=NEW_ACCOUNT, headers=_bearer(token))
    assert r.status_code == 403


def test_una_cuenta_con_el_correo_repetido_da_409(client, segundo_factor, admin, db):
    token = _verificar_admin_users(client, db, admin)
    repetida = {**NEW_ACCOUNT, "email": ADMIN["email"]}
    r = client.post("/api/v1/auth/users", json=repetida, headers=_bearer(token))
    assert r.status_code == 409


def test_solo_se_crean_cuentas_de_inspector_o_administrador(client, segundo_factor, admin, db):
    """El schema no admite Ciudadano: 422 con el formato uniforme de error."""
    token = _verificar_admin_users(client, db, admin)
    r = client.post(
        "/api/v1/auth/users", json={**NEW_ACCOUNT, "role": "CIUDADANO"},
        headers=_bearer(token),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_un_inspector_creado_puede_iniciar_sesion_pero_no_usar_mfa(
    client, segundo_factor, admin, db
):
    """Límite real del dominio (RN-07): solo ADMINISTRADOR es cuenta administrativa."""
    token = _verificar_admin_users(client, db, admin)
    creada = client.post("/api/v1/auth/users", json=NEW_ACCOUNT, headers=_bearer(token))
    assert creada.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": NEW_ACCOUNT["email"],
              "password": creada.json()["temporary_password"]},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"        # el Inspector SÍ entra
    assert login.json()["mfa_required"] is False
    r = client.post(
        "/api/v1/auth/mfa/request", json={"purpose": ADMIN_USERS},
        headers=_bearer(login.json()["access_token"]),
    )
    assert r.status_code == 403                          # pero no puede usar MFA


# ------------------------------------------- formato uniforme de los errores
def test_los_errores_de_validacion_usan_el_formato_estandar(client, segundo_factor):
    """Un cuerpo inválido responde `{"error": {...}}`, no el `{"detail": [...]}`."""
    r = client.post("/api/v1/auth/login", json={"email": "no-es-correo"})
    assert r.status_code == 422
    body = r.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "validation_error"
    assert "password" in body["error"]["message"]          # dice qué campo falta
    assert isinstance(body["error"]["message"], str)       # un mensaje, no una lista


def test_el_registro_invalido_responde_el_formato_estandar(client, segundo_factor):
    r = client.post(
        "/api/v1/auth/register",
        json={"full_name": "ab", "email": "camila@mail.com", "password": "corta",
              "roles": ["ADMINISTRADOR"], "neighborhood": "Cuba"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
