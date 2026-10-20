"""
CU-03 · Flujo E: el segundo factor no está disponible.

E3 es tajante: "si el servicio del segundo factor no está disponible, la operación
NO se autoriza". La entidad ya lo resuelve (`MfaChallenge.fail_on_service_unavailable`
deja el desafío BLOQUEADO y lanza), y este caso de uso lo aplica a la operación en
curso, guarda el bloqueo y publica el evento para la auditoría (CU-05).

No reintenta solo: quien autoriza una operación crítica decide cuándo volver a
intentarlo, con un desafío nuevo.
"""
from dataclasses import dataclass

from prevenred.identity.domain.repositories import MfaChallengeRepository
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ConflictError, ForbiddenError


@dataclass(frozen=True)
class ServiceUnavailableCommand:
    """Usuario y operación cuya verificación quedó imposible de completar."""
    user_id: str
    purpose: str


class ResetMfaOnServiceUnavailable:
    """CU-03 E3: ante una caída del servicio, cierra el desafío y niega el avance."""

    def __init__(self, challenges: MfaChallengeRepository, events: EventBus) -> None:
        self._challenges, self._events = challenges, events

    def execute(self, cmd: ServiceUnavailableCommand) -> None:
        """Bloquea el desafío pendiente y NIEGA la operación (no devuelve nada útil).

        Siempre termina lanzando: sin poder comprobar el segundo factor, la
        operación crítica no se autoriza (E3), y "no poder comprobarlo" nunca es
        un permiso. El bloqueo queda guardado y auditado antes de lanzar.
        """
        challenge = self._challenges.get_pending_by_user(cmd.user_id, cmd.purpose)
        if challenge is None:
            raise ConflictError(
                "No hay una verificación en curso. Repite la operación cuando el "
                "servicio de verificación esté disponible."
            )
        try:
            challenge.fail_on_service_unavailable()
        finally:
            self._challenges.update(challenge)
            for event in challenge.pull_events():
                self._events.publish(event)
        raise ForbiddenError(
            "El servicio de verificación no está disponible en este momento. "
            "La operación no se autorizó."
        )
