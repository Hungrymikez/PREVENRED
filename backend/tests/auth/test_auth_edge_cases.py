"""Caja blanca de identidad: cada guard clause de CU-01/CU-02 y de la sesión (401/403/404/429)."""

from datetime import timedelta

import jwt
import pytest

from prevenred.auth.application.register_user import RegisterUser, RegisterUserCommand
from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import MAX_FAILED_LOGINS, User
from prevenred.auth.domain.value_objects import Email, validate_password_strength
from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.auth.infrastructure.jwt_token_service import JwtTokenService
from prevenred.auth.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.config import get_settings
from prevenred.shared.infrastructure.event_bus import InMemoryEventBus

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
PASSWORD = "clave-segura-1"


def _seed_user(db, *, email="ana@mail.com", role=Role.CIUDADANO, **changes) -> User:
    user = User.register(
        email=Email(email),
        raw_password=PASSWORD,
        name="Ana Gómez",
        role=role,
        hasher=Argon2PasswordHasher(),
    )
    for field, value in changes.items():
        setattr(user, field, value)
    repo = MongoUserRepository(db)
    repo.add(user)
    repo.update(user)
    return user


def _login(client, email="ana@mail.com", password=PASSWORD):
    return client.post(LOGIN, json={"email": email, "password": password})


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- CU-02: guard clauses del inicio de sesión ----------


def test_correo_malformado_responde_401_generico(client, db):
    _seed_user(db)
    malformed = _login(client, email="no-es-correo")
    wrong_pwd = _login(client, password="otra-clave-1")
    assert malformed.status_code == wrong_pwd.status_code == 401
    assert malformed.json() == wrong_pwd.json()  # no revela si el correo existe


def test_cuenta_bloqueada_responde_429_aun_con_clave_correcta(client, db):
    _seed_user(db, locked_until=utcnow() + timedelta(minutes=5))
    r = _login(client)
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "too_many_attempts"


def test_bloqueo_vencido_permite_iniciar_sesion(client, db):
    _seed_user(db, locked_until=utcnow() - timedelta(seconds=1))
    assert _login(client).status_code == 200


def test_umbral_de_bloqueo_es_exactamente_max_intentos(client, db):
    _seed_user(db)
    for _ in range(MAX_FAILED_LOGINS - 1):
        assert _login(client, password="mala-clave-1").status_code == 401
    assert _login(client).status_code == 200  # 4 fallos: aún no bloquea y reinicia contador

    for _ in range(MAX_FAILED_LOGINS):
        _login(client, password="mala-clave-1")
    assert _login(client).status_code == 429  # 5 fallos: bloqueo


def test_cuenta_desactivada_responde_403(client, db):
    _seed_user(db, is_active=False)
    r = _login(client)
    assert r.status_code == 403
    assert "desactivada" in r.json()["error"]["message"]


def test_cuenta_administrativa_exige_mfa_403(client, db):
    _seed_user(db, email="admin@pereira.gov.co", role=Role.ADMIN)
    r = _login(client, email="admin@pereira.gov.co")
    assert r.status_code == 403
    assert "dos pasos" in r.json()["error"]["message"]


# ---------- Sesión: token inválido / cuenta eliminada ----------


def _token(**claims) -> str:
    s = get_settings()
    return jwt.encode(
        {"exp": utcnow() + timedelta(minutes=5), "iat": utcnow(), **claims},
        s.jwt_secret,
        algorithm=s.jwt_algorithm,
    )


@pytest.mark.parametrize(
    "token",
    [
        "no.es.un.jwt",
        _token(sub="64b7f0c2a1b2c3d4e5f60718", role="rol-inexistente"),  # ValueError
        _token(role="ciudadano"),  # KeyError: falta 'sub'
    ],
)
def test_token_invalido_responde_401(client, token):
    r = client.get(ME, headers=_bearer(token))
    assert r.status_code == 401


def test_me_de_cuenta_eliminada_responde_404(client, db):
    _seed_user(db)
    token = _login(client).json()["access_token"]
    db["users"].delete_many({})
    r = client.get(ME, headers=_bearer(token))
    assert r.status_code == 404


def test_endpoint_protegido_con_cuenta_eliminada_responde_401(api, db):
    user = _seed_user(db)
    token = JwtTokenService(get_settings()).issue(user.id, user.role)
    db["users"].delete_many({})
    r = api.get("/api/v1/volunteering/assignments/my", headers=_bearer(token))
    assert r.status_code == 401


# ---------- Value objects y fábrica User.register ----------


@pytest.mark.parametrize("raw", ["", "sin-arroba.com", "a@b", "a b@c.com", "a@@b.com"])
def test_email_invalido(raw):
    with pytest.raises(ValidationError):
        Email(raw)


def test_email_se_normaliza():
    assert Email("  Ana@MAIL.com ").value == "ana@mail.com"


@pytest.mark.parametrize(("password", "ok"), [("1234567", False), ("12345678", True)])
def test_politica_de_contrasena_limite_8(password, ok):
    if ok:
        validate_password_strength(password)
    else:
        with pytest.raises(ValidationError):
            validate_password_strength(password)


def test_registro_con_clave_corta_por_caso_de_uso(db):
    use_case = RegisterUser(MongoUserRepository(db), Argon2PasswordHasher(), InMemoryEventBus())
    with pytest.raises(ValidationError):
        use_case.execute(
            RegisterUserCommand(
                full_name="Ana Gómez",
                email="ana@mail.com",
                password="corta",
                role=Role.CIUDADANO,
                neighborhood="Cuba",
                privacy_notice_version="v1",
                accepted_terms=True,
            )
        )


def test_register_sin_clave_deja_hash_inutilizable():
    user = User.register(full_name="Ana Gómez", email=Email("a@b.co"), role=Role.CIUDADANO)
    assert user.password_hash == "unusable_hash"


@pytest.mark.parametrize(
    ("full_name", "neighborhood"), [("Al", "Cuba"), ("   ", "Cuba"), ("Ana Gómez", "   ")]
)
def test_register_valida_nombre_y_barrio(full_name, neighborhood):
    with pytest.raises(ValidationError):
        User.register(
            full_name=full_name,
            email=Email("a@b.co"),
            role=Role.CIUDADANO,
            neighborhood=neighborhood,
        )


def test_autoregistro_de_inspector_sin_hasher_es_403():
    with pytest.raises(ForbiddenError):
        User.register(full_name="Ana Gómez", email=Email("a@b.co"), role=Role.INSPECTOR)


def test_endpoint_protegido_con_token_valido_resuelve_el_usuario_real(api, db):
    user = _seed_user(db)
    token = JwtTokenService(get_settings()).issue(user.id, user.role)
    r = api.get("/api/v1/volunteering/assignments/my", headers=_bearer(token))
    assert r.status_code == 200
    assert r.json() == []
