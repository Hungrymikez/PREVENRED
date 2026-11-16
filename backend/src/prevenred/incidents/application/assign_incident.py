"""CU-39 · Asignar un incidente a un Inspector (solo Administrador)."""

from dataclasses import dataclass

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role
from prevenred.shared.domain.errors import ForbiddenError, NotFoundError, ValidationError

from ..domain.incident import Incident
from ..domain.repositories import IncidentRepository


@dataclass(frozen=True)
class AssignIncidentCommand:
    """Datos de entrada. `assignee_role` lo resuelve la interfaz consultando la cuenta
    (None si no existe o está inactiva), para no depender del interior de identity."""

    incident_id: str
    assignee_id: str
    assignee_role: Role | None
    notes: str
    operator: TokenPayload


class AssignIncident:
    """Caso de uso: el Administrador asigna el caso a un Inspector activo."""

    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def execute(self, command: AssignIncidentCommand) -> Incident:
        if command.operator.role != Role.ADMINISTRADOR:
            raise ForbiddenError("Solo un administrador puede asignar casos.")
        if command.assignee_role != Role.INSPECTOR:
            raise ValidationError("El caso solo se puede asignar a un inspector activo.")

        incident = self._repository.get_by_id(command.incident_id)
        if incident is None:
            raise NotFoundError(f"Incidente con ID '{command.incident_id}' no encontrado.")

        incident.assign(
            assignee_id=command.assignee_id,
            changed_by=command.operator.user_id,
            notes=command.notes.strip(),
        )
        self._repository.save(incident)
        return incident
