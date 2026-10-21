"""CU-29 · Reportar incidente de emergencia."""

from dataclasses import dataclass

from prevenred.auth.application.ports import TokenPayload
from prevenred.shared.application.event_bus import EventBus

from ..domain.events import IncidentReportedEvent
from ..domain.incident import Incident, IncidentSeverity, IncidentType
from ..domain.repositories import IncidentRepository


@dataclass(frozen=True)
class ReportIncidentCommand:
    """Datos de entrada del reporte (sin detalles HTTP)."""

    incident_type: IncidentType
    severity: IncidentSeverity
    description: str
    longitude: float
    latitude: float
    reporter: TokenPayload
    media_urls: list[str] | None = None


class ReportIncident:
    """Caso de uso CU-29: crea un reporte de emergencia georreferenciado."""

    def __init__(self, repository: IncidentRepository, event_bus: EventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    def execute(self, command: ReportIncidentCommand) -> Incident:
        incident = Incident.create(
            incident_type=command.incident_type,
            severity=command.severity,
            description=command.description,
            longitude=command.longitude,
            latitude=command.latitude,
            reported_by=command.reporter.user_id,
            media_urls=command.media_urls,
        )
        self._repository.save(incident)
        self._event_bus.publish(
            IncidentReportedEvent(
                incident_id=incident.id,
                case_number=incident.case_number,
                incident_type=incident.incident_type,
                reported_by=incident.reported_by,
                occurred_at=incident.created_at,
            )
        )
        return incident
