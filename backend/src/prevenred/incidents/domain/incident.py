"""Entidad Incident: reportes de emergencia (CU-29, CU-30, CU-39; RF-22..24)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.ids import EntityId, new_id


class IncidentType(StrEnum):
    """Tipos de reporte de emergencia."""

    VIA_BLOQUEADA = "VIA_BLOQUEADA"
    DESLIZAMIENTO = "DESLIZAMIENTO"
    INUNDACION = "INUNDACION"
    DANO_ESTRUCTURAL = "DANO_ESTRUCTURAL"
    VIVIENDA_DANADA = "VIVIENDA_DANADA"
    OTRO = "OTRO"


class IncidentSeverity(StrEnum):
    """Gravedad del incidente."""

    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class IncidentStatus(StrEnum):
    """Ciclo de vida del incidente (5 estados del catálogo)."""

    REPORTED = "REPORTADO"
    IN_REVIEW = "EN_REVISION"
    ASSIGNED = "ASIGNADO"
    IN_PROGRESS = "EN_ATENCION"
    RESOLVED = "RESUELTO"


@dataclass(frozen=True)
class IncidentStatusTransition:
    """Entrada de historial de cambio de estado."""

    previous_status: IncidentStatus
    new_status: IncidentStatus
    changed_by: EntityId
    changed_at: datetime
    notes: str


@dataclass(kw_only=True, eq=False)
class Incident(Entity):
    """Reporte de emergencia con ubicación GeoJSON y trazabilidad de estados."""

    case_number: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    description: str
    longitude: float
    latitude: float
    reported_by: EntityId
    media_urls: list[str]
    created_at: datetime
    history: list[IncidentStatusTransition] = field(default_factory=list)
    assigned_to: EntityId | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        description: str,
        longitude: float,
        latitude: float,
        reported_by: EntityId,
        media_urls: list[str] | None = None,
    ) -> "Incident":
        """Crea un reporte en estado REPORTADO (CU-29)."""
        cleaned_desc = description.strip() if description else ""
        if len(cleaned_desc) < 5:
            raise ValidationError(
                "La descripción del incidente debe contener al menos 5 caracteres."
            )
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise ValidationError("Coordenadas geográficas inválidas.")

        now = utcnow()
        incident_id = new_id()
        case_num = f"INC-{now.strftime('%Y%m%d')}-{incident_id[:6].upper()}"

        return cls(
            id=incident_id,
            case_number=case_num,
            incident_type=incident_type,
            severity=severity,
            status=IncidentStatus.REPORTED,
            description=cleaned_desc,
            longitude=longitude,
            latitude=latitude,
            reported_by=reported_by,
            media_urls=list(media_urls or []),
            created_at=now,
            history=[],
            updated_at=now,
        )

    def transition_status(
        self,
        *,
        new_status: IncidentStatus,
        changed_by: EntityId,
        notes: str = "",
    ) -> None:
        """Registra un cambio de estado (CU-39)."""
        if self.status == new_status:
            raise ValidationError(f"El incidente ya se encuentra en estado {new_status.value}.")

        now = utcnow()
        self.history.append(
            IncidentStatusTransition(
                previous_status=self.status,
                new_status=new_status,
                changed_by=changed_by,
                changed_at=now,
                notes=notes.strip(),
            )
        )
        self.status = new_status
        self.updated_at = now
