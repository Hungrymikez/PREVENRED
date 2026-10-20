"""
Entidades del censo de inmuebles: `Property` e `Inspection`.

Por qué: la visita de campo se hace OFFLINE en zonas sin red (CU-37). El celular
genera un `client_id` único por registro; al sincronizar, ese id evita duplicar
el inmueble o la inspección si la petición se reintenta. La ubicación se guarda
como GeoJSON Point para poder buscarla en el mapa (índice 2dsphere).
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_one_of, require_text, require_utc

#: Estados del inmueble durante el censo (provisional; el catálogo es CU-34).
PROPERTY_STATUSES = ("REGISTRADA", "EN_INSPECCION", "HABITABLE", "NO_HABITABLE")

#: Niveles de daño que evalúa el inspector (catálogo CU-35).
DAMAGE_LEVELS = ("LEVE", "MODERADO", "SEVERO", "COLAPSO")

#: Resultado de habitabilidad (CU-35).
HABITABILITY_STATUSES = ("HABITABLE", "HABITABLE_CON_OBSERVACIONES", "NO_HABITABLE")

#: Niveles que obligan a una segunda revisión (O-11: valor provisional).
CRITICAL_DAMAGE_LEVELS = ("SEVERO", "COLAPSO")


def _require_point(latitude: float, longitude: float) -> None:
    """Valida coordenadas antes de armar el GeoJSON (evita documentos inservibles en el mapa)."""
    if not -90 <= latitude <= 90:
        raise ValidationError("La latitud debe estar entre -90 y 90.")
    if not -180 <= longitude <= 180:
        raise ValidationError("La longitud debe estar entre -180 y 180.")


@dataclass(kw_only=True, eq=False)
class Property(Entity):
    """Inmueble censado por un inspector (CU-34)."""
    address: str
    latitude: float
    longitude: float
    created_by: str                        # quién lo censó
    residents_count: int = 0
    characteristics: dict = field(default_factory=dict)
    photos: tuple[str, ...] = ()           # ids de files
    status: str = PROPERTY_STATUSES[0]
    case_id: str | None = None             # consecutivo visible al ciudadano
    client_id: str | None = None           # id generado en el celular (CU-37)
    synced_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida los datos obligatorios del censo."""
        require_text(self.address, "address", max_length=300)
        require_text(self.created_by, "created_by", max_length=64)
        require_one_of(self.status, PROPERTY_STATUSES, "status")
        _require_point(self.latitude, self.longitude)
        if self.residents_count < 0:
            raise ValidationError("El número de residentes no puede ser negativo.")
        if self.synced_at is not None:
            self.synced_at = require_utc(self.synced_at, "synced_at")

    def add_photos(self, photo_ids: list[str]) -> None:
        """Agrega fotos sin duplicarlas (CU-34)."""
        self.photos = tuple(dict.fromkeys((*self.photos, *photo_ids)))

    def mark_synced(self, at: datetime) -> None:
        """Registra cuándo llegó al servidor (CU-37)."""
        self.synced_at = require_utc(at, "synced_at")

    def start_inspection(self) -> None:
        """Pasa a 'EN_INSPECCION' cuando el inspector la abre."""
        self.status = "EN_INSPECCION"

    def register_habitability(self, habitability: str) -> None:
        """Cierra el censo con el resultado del inspector (CU-35)."""
        require_one_of(habitability, HABITABILITY_STATUSES, "habitability")
        self.status = "HABITABLE" if habitability == "HABITABLE" else "NO_HABITABLE"



@dataclass(kw_only=True, eq=False)
class Inspection(Entity):
    """Inspección de habitabilidad de un inmueble (CU-35)."""
    property_id: str
    inspector_id: str
    damage_level: str
    habitability_status: str
    findings: str = ""
    evidence_files: tuple[str, ...] = ()
    protocol_version: str = "1"
    inspected_at: datetime = field(default_factory=utcnow)
    client_id: str | None = None
    synced_at: datetime | None = None
    second_review_by: str | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida la inspección y su coherencia con el nivel de daño."""
        require_text(self.property_id, "property_id", max_length=64)
        require_text(self.inspector_id, "inspector_id", max_length=64)
        require_one_of(self.damage_level, DAMAGE_LEVELS, "damage_level")
        require_one_of(self.habitability_status, HABITABILITY_STATUSES, "habitability_status")
        require_text(self.protocol_version, "protocol_version", max_length=20)
        self.inspected_at = require_utc(self.inspected_at, "inspected_at")
        # Coherencia: un daño severo/colapso no puede declararse habitable, porque
        # eso ocultaría un riesgo de vida para los residentes.
        if self.damage_level in CRITICAL_DAMAGE_LEVELS and self.habitability_status == "HABITABLE":
            raise ValidationError(
                "Con daño severo o colapso, el inmueble no puede quedar como habitable."
            )

    @property
    def requires_second_review(self) -> bool:
        """Los casos críticos se revisan dos veces (O-11)."""
        return self.damage_level in CRITICAL_DAMAGE_LEVELS

    def mark_synced(self, at: datetime) -> None:
        """Registra cuándo llegó al servidor (CU-37)."""
        self.synced_at = require_utc(at, "synced_at")

    def assign_second_review(self, reviewer_id: str) -> None:
        """Asigna al segundo revisor de un caso crítico (O-11)."""
        if not self.requires_second_review:
            raise ValidationError("Este caso no requiere segunda revisión.")
        require_text(reviewer_id, "second_review_by", max_length=64)
        if reviewer_id == self.inspector_id:
            raise ValidationError("La segunda revisión la debe hacer otra persona.")
        self.second_review_by = reviewer_id
