"""Pruebas del DOMINIO: rápidas, sin base de datos ni HTTP."""

import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import MAX_FAILED_LOGINS, User
from prevenred.identity.domain.value_objects import Email
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow


def _new(role=Role.CIUDADANO, accepted=True) -> User:
    return User.register(
        full_name="Camila Pérez",
        email=Email("Camila@Mail.com"),
        password_hash="x",
        role=role,
        neighborhood="Cuba",
        privacy_notice_version="v1",
        accepted_terms=accepted,
    )


def test_registro_normaliza_email_y_emite_evento():
    user = _new()
    assert user.email.value == "camila@mail.com"
    assert len(user.pull_events()) == 1


def test_sin_aceptar_terminos_no_se_crea_cuenta():  # CU-01 A1
    with pytest.raises(ValidationError):
        _new(accepted=False)


@pytest.mark.parametrize("role", [Role.INSPECTOR, Role.ADMINISTRADOR])
def test_no_hay_autoregistro_de_roles_internos(role):  # CU-01 / RN-07
    with pytest.raises(ForbiddenError):
        _new(role=role)


def test_bloqueo_tras_intentos_fallidos():  # CU-02 E2
    user, now = _new(), utcnow()
    for _ in range(MAX_FAILED_LOGINS):
        user.register_failed_login(now)
    assert user.is_locked(now)
