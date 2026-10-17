"""Pruebas del DOMINIO: rápidas, sin base de datos ni HTTP."""
import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import MAX_FAILED_LOGINS, User
from prevenred.identity.domain.value_objects import Email
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow


def _new(role=Role.CIUDADANO, accepted=True) -> User:
    return User.register(
        full_name="Camila Pérez", email=Email("Camila@Mail.com"), password_hash="x",
        role=role, neighborhood="Cuba", privacy_notice_version="v1", accepted_terms=accepted,
    )


def test_registro_normaliza_email_y_emite_evento():
    user = _new()
    assert user.email.value == "camila@mail.com"
    assert len(user.pull_events()) == 1


def test_sin_aceptar_terminos_no_se_crea_cuenta():  # CU-01 A1
    with pytest.raises(ValidationError):
        _new(accepted=False)


@pytest.mark.parametrize("role", [Role.INSPECTOR, Role.ADMINISTRADOR, Role.PROFESIONAL_SALUD])
def test_no_hay_autoregistro_de_roles_internos(role):  # CU-01 / RN-07
    with pytest.raises(ForbiddenError):
        _new(role=role)


@pytest.mark.parametrize("role", [Role.CIUDADANO, Role.TECNICO, Role.VOLUNTARIO])
def test_se_autoregistran_ciudadano_tecnico_y_voluntario(role):  # CU-01
    assert role.is_self_registrable
    assert _new(role=role).role is role


def test_los_tres_roles_restantes_no_se_autoregistran():
    for role in (Role.PROFESIONAL_SALUD, Role.INSPECTOR, Role.ADMINISTRADOR):
        assert not role.is_self_registrable


def test_los_codigos_de_rol_van_en_mayuscula():
    assert list(Role) == [
        Role.CIUDADANO, Role.TECNICO, Role.VOLUNTARIO,
        Role.PROFESIONAL_SALUD, Role.INSPECTOR, Role.ADMINISTRADOR,
    ]
    assert all(r.value == r.name for r in Role)


# ---- CU-08 A1: el Administrador sí puede crear cuentas internas ----
@pytest.mark.parametrize("role", [Role.INSPECTOR, Role.ADMINISTRADOR])
def test_cuenta_interna_se_crea_por_encargo_de_un_administrador(role):
    user = User.open_administratively(
        full_name="Iván Inspector", email=Email("Ivan@PrevenRed.gov.co"),
        password_hash="hash", role=role, neighborhood="Cuba",
        privacy_notice_version="v1", created_by="a" * 24,
    )
    assert user.role is role and user.is_active
    assert user.email.value == "ivan@prevenred.gov.co"
    event = user.pull_events()[0]
    # Evento propio: NO `UserRegistered` (no es un técnico pendiente de CU-17).
    assert type(event).__name__ == "UserAccountCreated"
    assert event.created_by == "a" * 24 and event.role == role.value


def test_desde_administracion_no_se_crean_cuentas_de_la_comunidad():
    with pytest.raises(ValidationError):
        User.open_administratively(
            full_name="Ciudadano", email=Email("c@mail.com"), password_hash="h",
            role=Role.CIUDADANO, neighborhood="Cuba",
            privacy_notice_version="v1", created_by="a" * 24,
        )


def test_bloqueo_tras_intentos_fallidos():  # CU-02 E2
    user, now = _new(), utcnow()
    for _ in range(MAX_FAILED_LOGINS):
        user.register_failed_login(now)
    assert user.is_locked(now)
