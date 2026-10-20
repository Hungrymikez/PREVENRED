"""Pruebas del DOMINIO de CU-03 (verificación reforzada): sin base de datos ni HTTP."""
from datetime import timedelta

import pytest

from prevenred.identity.domain.events import (
    MfaEnabled,
    MfaVerificationFailed,
    MfaVerificationLocked,
    MfaVerified,
)
from prevenred.identity.domain.mfa import (
    CODE_TTL,
    MFA_MAX_ATTEMPTS,
    MIN_RETRY_AFTER,
    MfaChallenge,
    MfaSettings,
)
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.value_objects import OneTimeCode, SecondFactorMethod
from prevenred.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    TooManyAttemptsError,
    UnauthorizedError,
    ValidationError,
)
from prevenred.shared.domain.events import utcnow

_CODE = OneTimeCode("482913")
_OTHER = OneTimeCode("111111")
_SECRET = "secreto-cifrado"


def _challenge(role=Role.ADMINISTRADOR, now=None) -> tuple[MfaChallenge, object]:
    moment = now or utcnow()
    return (
        MfaChallenge.open(
            user_id="a" * 24,
            role=role,
            purpose="cambio_de_modo",
            method=SecondFactorMethod("totp"),
            code_hash=str(_CODE),
            secret_enc=_SECRET,
            now=moment,
        ),
        moment,
    )


# ---- Value objects ----

def test_codigo_exige_seis_digitos():
    with pytest.raises(ValidationError):
        OneTimeCode("12345")
    with pytest.raises(ValidationError):
        OneTimeCode("abcdef")


def test_codigo_generado_es_valido_y_comparable():
    code = OneTimeCode.generate()
    assert len(code.value) == 6 and code.value.isdigit()
    assert code.mismo_valor_que(OneTimeCode(code.value))
    assert not code.mismo_valor_que(None)


def test_metodo_del_segundo_factor_se_normaliza():
    assert str(SecondFactorMethod("sms")) == "SMS"
    with pytest.raises(ValidationError):
        SecondFactorMethod("paloma")


# ---- CU-03 paso 1: abrir el desafío ----

def test_abrir_desafio_deja_codigo_vigente():
    challenge, moment = _challenge()
    assert challenge.status == "PENDIENTE"
    assert challenge.expires_at == moment + CODE_TTL
    assert not challenge.is_satisfied
    assert not challenge.is_expired(moment)


def test_solo_administradores_usan_mfa():  # RN-07
    with pytest.raises(ForbiddenError):
        _challenge(role=Role.INSPECTOR)


# ---- CU-03 paso 3: validar correcto, vigente y de un solo uso ----

def test_codigo_correcto_satisface_la_verificacion():
    challenge, moment = _challenge()
    challenge.verify(_CODE, now=moment + timedelta(seconds=30), code_matches=True)
    assert challenge.is_satisfied
    assert challenge.verified_at is not None
    event = challenge.pull_events()[0]
    assert isinstance(event, MfaVerified)
    assert event.purpose == "cambio_de_modo"


def test_codigo_incorrecto_permite_reintentar():  # E1
    challenge, moment = _challenge()
    with pytest.raises(UnauthorizedError):
        challenge.verify(_OTHER, now=moment, code_matches=False)
    assert not challenge.is_satisfied
    assert challenge.attempts == 1
    assert isinstance(challenge.pull_events()[0], MfaVerificationFailed)
    # Acierta en el segundo intento: el reintento servía.
    challenge.verify(_CODE, now=moment, code_matches=True)
    assert challenge.is_satisfied


def test_texto_mal_formado_cuenta_como_intento_fallido():
    challenge, moment = _challenge()
    with pytest.raises(UnauthorizedError):
        challenge.verify(OneTimeCode.parse("12ab"), now=moment, code_matches=False)
    assert challenge.attempts == 1


def test_codigo_vencido_no_se_acepta():  # A1 / paso 3
    challenge, moment = _challenge()
    with pytest.raises(UnauthorizedError):
        challenge.verify(_CODE, now=moment + CODE_TTL, code_matches=False)
    assert challenge.status == "EXPIRADO"
    assert not challenge.is_satisfied


def test_codigo_es_de_un_solo_uso():
    challenge, moment = _challenge()
    challenge.verify(_CODE, now=moment, code_matches=True)
    # Criterio de aceptación: una verificación no sirve para una segunda operación.
    with pytest.raises(ConflictError):
        challenge.verify(_CODE, now=moment, code_matches=True)


# ---- CU-03 E2: intentos agotados ----

def test_intentos_agotados_bloquean_la_operacion():  # E2
    challenge, moment = _challenge()
    for _ in range(MFA_MAX_ATTEMPTS - 1):
        with pytest.raises(UnauthorizedError):
            challenge.verify(_OTHER, now=moment, code_matches=False)
    with pytest.raises(TooManyAttemptsError):
        challenge.verify(_OTHER, now=moment, code_matches=False)
    assert challenge.is_locked_out()
    assert isinstance(challenge.pull_events()[-1], MfaVerificationLocked)
    # Bloqueado: ni el código correcto autoriza la operación.
    with pytest.raises(TooManyAttemptsError):
        challenge.verify(_CODE, now=moment, code_matches=True)
    assert not challenge.is_satisfied


# ---- CU-03 A1: pedir un código nuevo ----

def test_pedir_codigo_nuevo_tras_vencer():  # A1
    challenge, moment = _challenge()
    later = moment + CODE_TTL + MIN_RETRY_AFTER
    challenge.request_new_code(new_code_hash=str(_OTHER), now=later)
    assert challenge.status == "PENDIENTE"
    assert challenge.expires_at == later + CODE_TTL
    assert challenge.attempts == 0
    challenge.verify(_OTHER, now=later, code_matches=True)
    assert challenge.is_satisfied


def test_no_se_puede_pedir_codigo_de_inmediato():  # A1 (antivigencia)
    challenge, moment = _challenge()
    with pytest.raises(TooManyAttemptsError):
        challenge.request_new_code(new_code_hash=str(_OTHER), now=moment)


def test_no_se_piden_codigos_despues_de_bloquear():  # E2 no se salta por A1
    challenge, moment = _challenge()
    for _ in range(MFA_MAX_ATTEMPTS):
        with pytest.raises((UnauthorizedError, TooManyAttemptsError)):
            challenge.verify(_OTHER, now=moment, code_matches=False)
    with pytest.raises(TooManyAttemptsError):
        challenge.request_new_code(
            new_code_hash=str(_OTHER), now=moment + CODE_TTL + MIN_RETRY_AFTER
        )


# ---- CU-03 E3: servicio del segundo factor no disponible ----

def test_sin_servicio_la_operacion_no_se_autoriza():  # E3
    challenge, moment = _challenge()
    challenge.fail_on_service_unavailable()
    assert challenge.is_locked_out()
    assert not challenge.is_satisfied
    with pytest.raises(TooManyAttemptsError):
        challenge.verify(_CODE, now=moment, code_matches=True)


# ---- RN-07: configuración del segundo factor ----

def test_activar_segundo_factor_emite_evento():
    settings = MfaSettings(user_id="a" * 24)
    assert not settings.is_configured
    settings.enable(secret_enc="cifrado", method=SecondFactorMethod("TOTP"))
    assert settings.is_configured
    assert isinstance(settings.pull_events()[0], MfaEnabled)


def test_segundo_factor_activo_exige_secreto():
    with pytest.raises(ValidationError):
        MfaSettings(user_id="a" * 24, enabled=True)


def test_administrador_no_puede_apagar_mfa():  # RN-07
    settings = MfaSettings(user_id="a" * 24)
    settings.enable(secret_enc="cifrado", method=SecondFactorMethod("TOTP"))
    with pytest.raises(ForbiddenError):
        settings.disable(role=Role.ADMINISTRADOR)
    assert settings.is_configured


def test_otro_rol_puede_apagar_mfa():
    settings = MfaSettings(user_id="a" * 24)
    settings.enable(secret_enc="cifrado", method=SecondFactorMethod("TOTP"))
    settings.disable(role=Role.CIUDADANO)
    assert not settings.is_configured
