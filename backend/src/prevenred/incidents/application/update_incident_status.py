"""CU-39 · Actualizar estado de un incidente."""

from dataclasses import dataclass

from prevenred.auth.application.ports import TokenPayload
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ForbiddenError, NotFoundError

from ..domain.events import IncidentStatusChangedEvent
from ..domain.incident import Incident, IncidentStatus
from ..domain.repositories import IncidentRepository

_STAFF_ROLES = frozenset({"administrador", "inspector"})


@dataclass(frozen=True)
class UpdateIncidentStatusCommand:
    """Datos de entrada para cambiar el estado."""

    incident_id: str
    new_status: IncidentStatus
    notes: str
    operator: TokenPayload


class UpdateIncidentStatus:
    """Caso de uso CU-39: solo personal autorizado cambia el estado."""

    def __init__(self, repository: IncidentRepository, event_bus: EventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    def execute(self, command: UpdateIncidentStatusCommand) -> Incident:
        if command.operator.role.value not in _STAFF_ROLES:
            raise ForbiddenError(
                "Solo personal autorizado puede actualizar el estado de incidentes."
            )

        incident = self._repository.get_by_id(command.incident_id)
        if incident is None:
            raise NotFoundError(f"Incidente con ID '{command.incident_id}' no encontrado.")

        previous = incident.status
        incident.transition_status(
            new_status=command.new_status,
            changed_by=command.operator.user_id,
            notes=command.notes,
        )
        self._repository.save(incident)
        self._event_bus.publish(
            IncidentStatusChangedEvent(
                incident_id=incident.id,
                previous_status=previous,
                new_status=incident.status,
                changed_by=command.operator.user_id,
            )
        )
        return incident
