"""
Entidad Incident: reporte de emergencia (CU-29, CU-30, CU-32, CU-39).

Reglas clave que viven aquí:
  - GRAVEDAD: el reportante elige uno de los niveles del catálogo; no inventa texto.
  - DUPLICADOS: un reporte puede marcarse como duplicado de otro (`duplicate_of`).
    El duplicado NO se borra: se conserva para auditoría, pero el tablero muestra
    solo los principales (el problema central del proyecto es no contar dos veces).
  - UBICACIÓN: GeoJSON Point, siempre en la zona del reportante.
  - OFFLINE: `client_id` hace idempotente la sincronización (CU-37).
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_one_of, require_text, require_utc

#: Tipos de emergencia reportables (CU-29, catálogo tipo incidente).
INCIDENT_TYPES = (
    "VIVIENDA_DANADA",
    "VIA_BLOQUEADA",
    "DESLIZAMIENTO",
    "INUNDACION",
    "SERVICIOS_AFECTADOS",
    "OTRO",
)

#: Los 5 estados del tablero (catálogo estado incidente).
INCIDENT_STATUSES = (
    "REPORTADO",
    "EN_VERIFICACION",
    "ASIGNADO",
    "EN_ATENCION",
    "CERRADO",
)

#: Prioridad operativa.
PRIORITIES = ("BAJA", "MEDIA", "ALTA", "CRITICA")

#: Gravedad percibida por el reportante.
SEVERITIES = ("LEVE", "MODERADA", "ALTA", "MUY_ALTA")

#: Estados sin retorno: un reporte cerrado no vuelve a abrirse por esta vía
#: (si el riesgo reaparece, se crea un reporte nuevo con su propia fecha).
CLOSED_STATUS = "CERRADO"


@dataclass(kw_only=True, eq=False)
class Incident(Entity):
    """Reporte de emergencia realizado por un ciudadano."""
    type: str
    description: str
    latitude: float
    longitude: float
    reported_by: str                       # cuenta que reporta
    status: str = "REPORTADO"
    priority: str = "MEDIA"
    severity: str = "MODERADA"
    needs: tuple[str, ...] = ()
    photos: tuple[str, ...] = ()           # ids de files (opcionales, O-13)
    assigned_to: str | None = None
    case_id: str | None = None
    reported_at: datetime = field(default_factory=utcnow)   # hora del celular
    client_id: str | None = None
    duplicate_of: str | None = None
    property_id: str | None = None
    updated_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)    # llegada al servidor

    def __post_init__(self) -> None:
        """Valida el reporte: un reporte sin tipo ni ubicación es inservible."""
        require_one_of(self.type, INCIDENT_TYPES, "type")
        require_text(self.description, "description", max_length=1000)
        require_one_of(self.status, INCIDENT_STATUSES, "status")
        require_one_of(self.priority, PRIORITIES, "priority")
        require_one_of(self.severity, SEVERITIES, "severity")
        if not -90 <= self.latitude <= 90:
            raise ValidationError("La latitud debe estar entre -90 y 90.")
        if not -180 <= self.longitude <= 180:
            raise ValidationError("La longitud debe estar entre -180 y 180.")
        self.reported_at = require_utc(self.reported_at, "reported_at")
        if self.updated_at is not None:
            self.updated_at = require_utc(self.updated_at, "updated_at")

    # ---- Duplicados (el punto central del proyecto) ----
    def mark_as_duplicate(self, primary_id: str) -> None:
        """Marca este reporte como duplicado de otro (CU-30).

        No se borra: se conserva la evidencia de que la persona reportó, pero deja
        de contarse en los indicadores.
        """
        require_text(primary_id, "duplicate_of", max_length=64)
        if primary_id == self.id:
            raise ValidationError("Un reporte no puede ser duplicado de sí mismo.")
        self.duplicate_of = primary_id

    @property
    def is_duplicate(self) -> bool:
        """True si ya se identificó un reporte principal para este caso."""
        return self.duplicate_of is not None

    # ---- Asignación y atención (CU-32, CU-39) ----
    def assign_to(self, user_id: str) -> None:
        """Asigna el reporte a un técnico o funcionario (CU-32)."""
        require_text(user_id, "assigned_to", max_length=64)
        if self.status == CLOSED_STATUS:
            raise ForbiddenError("Este reporte ya está cerrado.")
        self.assigned_to = user_id
        self.status = "ASIGNADO"
        self.touch()

    def change_status(self, status: str) -> None:
        """Cambia el estado respetando el cierre definitivo (CU-39)."""
        require_one_of(status, INCIDENT_STATUSES, "status")
        if self.status == CLOSED_STATUS and status != CLOSED_STATUS:
            raise ForbiddenError("Un reporte cerrado no se puede reabrir.")
        self.status = status
        self.touch()

    def set_priority(self, priority: str) -> None:
        """Ajusta la prioridad operativa (la decide el centro de coordinación)."""
        require_one_of(priority, PRIORITIES, "priority")
        self.priority = priority
        self.touch()

    def close(self) -> None:
        """Cierra el reporte: la atención terminó (CU-39)."""
        self.status = CLOSED_STATUS
        self.touch()

    # ---- Evidencias ----
    def add_photos(self, photo_ids: list[str]) -> None:
        """Adjunta fotos sin duplicar ids (O-13: la foto es opcional)."""
        self.photos = tuple(dict.fromkeys((*self.photos, *photo_ids)))

    def touch(self) -> None:
        """Marca la última modificación (se muestra 'actualizado hace…')."""
        self.updated_at = utcnow()
