"""
CU-03 · Validar el segundo factor (flujo A).

Orquesta lo que la ficha pide, sin reglas propias: el dominio (`MfaChallenge`)
decide vigencia, intentos y uso único; este caso de uso consigue el secreto,
genera/valida el código a través del puerto técnico, guarda y publica eventos.

  paso 1   abrir el desafío de la operación y entregar el código
  paso 3   el código debe ser correcto, vigente y de un solo uso
  A1       pedir un código nuevo cuando el anterior venció
  E1       código incorrecto o vencido => reintentar (intentos limitados)
  E2       intentos agotados => bloquear la operación y registrar el evento
  E3       servicio del segundo factor caído => la operación NO se autoriza
"""
from dataclasses import dataclass
from datetime import datetime

from prevenred.identity.application.security import hash_one_time_code
from prevenred.identity.domain.mfa import CODE_TTL, MfaChallenge
from prevenred.identity.domain.repositories import (
    MfaChallengeRepository,
    SecondFactorGateway,
    UserRepository,
)
from prevenred.identity.domain.value_objects import OneTimeCode, SecondFactorMethod
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    TooManyAttemptsError,
)
from prevenred.shared.domain.events import utcnow


@dataclass(frozen=True)
class RequestMfaCommand:
    """Paso 1: quién pide el código y para qué operación."""
    user_id: str
    purpose: str
    method: SecondFactorMethod | None = None   # None => el método por defecto del puerto


@dataclass(frozen=True)
class MfaChallengeView:
    """Lo que se devuelve al pedir el código (ni el secreto ni el hash salen de aquí)."""
    challenge_id: str
    method: SecondFactorMethod
    code: OneTimeCode            # v1: se muestra/envía (el mecanismo final lo fija el doc 07)
    expires_at: datetime


@dataclass(frozen=True)
class VerifyMfaCommand:
    """Paso 3: quién entrega el código, para qué operación y cuál."""
    user_id: str
    purpose: str
    code: str


class RequestMfaCode:
    """CU-03 paso 1 / A1: entrega el código del segundo factor a una cuenta administrativa."""

    def __init__(
        self,
        users: UserRepository,
        challenges: MfaChallengeRepository,
        gateway: SecondFactorGateway,
        events: EventBus,
    ) -> None:
        self._users, self._challenges, self._gateway, self._events = (
            users, challenges, gateway, events
        )

    def execute(self, cmd: RequestMfaCommand) -> MfaChallengeView:
        """Abre el desafío y entrega el código.

        Reutiliza el desafío ABIERTO de esa operación; si venció, lo reemplaza
        (A1). No abre uno nuevo a la fuerza: eso permitiría saltarse el bloqueo
        por intentos de E2.
        """
        user = self._users.get_by_id(cmd.user_id)
        if user is None:
            raise NotFoundError("La cuenta ya no existe.")
        if not user.role.is_administrative:     # RN-07: se avisa antes de tocar nada
            raise ForbiddenError(
                "La verificación en dos pasos es solo para cuentas administrativas."
            )

        pending = self._challenges.get_pending_by_user(user.id, cmd.purpose)
        if pending is not None and not pending.is_expired(utcnow()):
            raise ConflictError(
                "Ya hay un código vigente para esta operación. "
                "Úsalo o pide uno nuevo cuando venza."
            )
        if pending is not None:                 # A1: el anterior venció
            self._challenges.expire_stale(user.id)

        # El método elegido manda; si no se pidió, se conserva el del desafío previo.
        if cmd.method is not None:
            method = cmd.method
        elif pending is not None:
            method = pending.method
        else:
            method = self._gateway.default_method()
        code, secret_enc = self._gateway.issue_code(
            secret_enc=user.mfa_secret_enc or "", code_hash=hash_one_time_code
        )
        if secret_enc != user.mfa_secret_enc:
            # El puerto generó el secreto (primer uso): se guarda YA cifrado.
            user.enable_mfa(secret_enc)
            self._users.update(user)
            for event in user.pull_events():      # MfaEnabled (RN-07)
                self._events.publish(event)

        challenge = MfaChallenge.open(
            user_id=user.id,
            role=user.role,
            purpose=cmd.purpose,
            method=method,
            code_hash=hash_one_time_code(str(code)),
            secret_enc=secret_enc,
        )
        self._challenges.add(challenge)
        return MfaChallengeView(
            challenge_id=challenge.id,
            method=challenge.method,
            code=code,
            expires_at=challenge.expires_at,
        )


class VerifyMfaCode:
    """CU-03 paso 3 (con A1/E1/E2/E3): valida el código y autoriza la operación."""

    def __init__(
        self,
        users: UserRepository,
        challenges: MfaChallengeRepository,
        gateway: SecondFactorGateway,
        events: EventBus,
    ) -> None:
        self._users, self._challenges, self._gateway, self._events = (
            users, challenges, gateway, events
        )

    def execute(self, cmd: VerifyMfaCommand) -> MfaChallenge:
        """Valida el código de la operación indicada.

        Devuelve el desafío SATISFECHO (paso 4). Lanza UnauthorizedError mientras
        queden intentos (E1, también si el código venció: A1 permite pedir otro),
        TooManyAttemptsError al agotarlos o si ya estaba bloqueado (E2), y
        ConflictError si no hay verificación en curso para esa operación.
        """
        user = self._users.get_by_id(cmd.user_id)
        if user is None:
            raise NotFoundError("La cuenta ya no existe.")
        if not user.role.is_administrative:      # RN-07
            raise ForbiddenError("Esta operación no pide verificación en dos pasos.")

        challenge = self._challenges.get_pending_by_user(user.id, cmd.purpose)
        if challenge is None:
            # E2: si la operación quedó bloqueada, se dice eso (y NO se invita a
            # abrir un desafío nuevo, que sería saltarse el bloqueo).
            recent = utcnow() - CODE_TTL
            if self._challenges.get_blocked_by_user(
                user.id, cmd.purpose, since=recent
            ) is not None:
                raise TooManyAttemptsError(
                    "Se bloquearon los intentos de verificación. "
                    "Comunícate con otro administrador."
                )
            raise ConflictError(
                "No hay una verificación en curso para esta operación. Pide un código."
            )

        code = OneTimeCode.parse(cmd.code)      # None si viene mal formado: cuenta
        # como intento fallido, sin distinguirlo de un código equivocado (E1).
        # La comparación vive en el puerto técnico y se hace sobre el HASH, en
        # tiempo constante; el dominio recibe el veredicto y decide qué hacer.
        matches = code is not None and self._gateway.matches(
            code=code, code_hash=challenge.code_hash
        )
        try:
            challenge.verify(code, code_matches=matches)
        finally:
            # E1/E2: el avance (o el bloqueo) se guarda y se audita SIEMPRE, incluso
            # cuando el código fue incorrecto y el dominio lanza.
            self._challenges.update(challenge)
            for event in challenge.pull_events():
                self._events.publish(event)
        return challenge
