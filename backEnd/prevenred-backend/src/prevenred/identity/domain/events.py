"""Eventos que publica el contexto identity."""
from dataclasses import dataclass

from prevenred.shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class UserRegistered(DomainEvent):
    """Lo escuchará `services` para crear el perfil 'Pendiente' del técnico (CU-01 paso 7)."""
    user_id: str
    role: str


@dataclass(frozen=True, kw_only=True)
class SessionRevoked(DomainEvent):
    """CU-02 A4: se cerró una sesión. `audit` lo usará para la trazabilidad (CU-05)."""
    user_id: str
    jti: str


# ---- CU-03 · autenticación reforzada (MFA) ----
# Se publican SIEMPRE, acierto o fallo: E2 pide "registra el evento (CU-05)" y el
# panel de seguridad necesita ver los intentos fallidos, no solo los buenos.

@dataclass(frozen=True, kw_only=True)
class MfaVerified(DomainEvent):
    """CU-03 paso 4: la verificación reforzada quedó satisfecha para la operación."""
    user_id: str
    challenge_id: str
    purpose: str


@dataclass(frozen=True, kw_only=True)
class MfaVerificationFailed(DomainEvent):
    """CU-03 E1: el código fue incorrecto o venció; la operación sigue bloqueada."""
    user_id: str
    challenge_id: str
    purpose: str
    attempts: int


@dataclass(frozen=True, kw_only=True)
class MfaVerificationLocked(DomainEvent):
    """CU-03 E2: se agotaron los intentos. `audit` lo registra (CU-05)."""
    user_id: str
    challenge_id: str
    purpose: str
    attempts: int


@dataclass(frozen=True, kw_only=True)
class MfaEnabled(DomainEvent):
    """RN-07: una cuenta administrativa quedó con el segundo factor configurado."""
    user_id: str
    method: str


# ---- CU-08 · gestión de usuarios y roles ----
# La auditoría (CU-05) es obligatoria: si no queda registrada, el cambio no se
# aplica (E3). Por eso el caso de uso publica el evento después de guardar.

@dataclass(frozen=True, kw_only=True)
class UserAccountCreated(DomainEvent):
    """CU-08 A1: un Administrador creó una cuenta de Inspector o de Administrador."""
    user_id: str
    role: str
    created_by: str


@dataclass(frozen=True, kw_only=True)
class UserRoleChanged(DomainEvent):
    """CU-08 paso 6: cambió el rol de una cuenta. `role` es el rol ANTERIOR."""
    user_id: str
    previous_role: str
    new_role: str
    changed_by: str


@dataclass(frozen=True, kw_only=True)
class UserSuspended(DomainEvent):
    """CU-08 A2: la cuenta quedó suspendida y sus sesiones se revocan."""
    user_id: str
    suspended_by: str


@dataclass(frozen=True, kw_only=True)
class UserReactivated(DomainEvent):
    """CU-08 paso 2: se vuelve a habilitar una cuenta suspendida."""
    user_id: str
    reactivated_by: str
