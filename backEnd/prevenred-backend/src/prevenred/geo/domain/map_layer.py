"""
Entidad MapLayer: capa geográfica autorizada (CU-10, CU-40).

Por qué existe: el mapa muestra riesgo, oferta de ayuda y vías, pero no todo el
mundo ve lo mismo. `visible_for_roles` dice qué roles pueden cargar la capa; el
ciudadano no ve, por ejemplo, la capa con ubicaciones de personas vulnerables.
La `version` permite invalidar la caché del celular cuando la fuente cambia.
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import (
    require_one_of,
    require_text,
    require_unique,
    require_utc,
)

#: Tipos de capa que sabe dibujar el mapa.
LAYER_TYPES = ("RIESGO", "OFERTA", "INFRAESTRUCTURA", "ZONAS", "OTRA")


@dataclass(kw_only=True, eq=False)
class MapLayer(Entity):
    """Fuente geográfica publicada para el mapa."""
    name: str
    type: str
    source: str                    # de dónde salió (dato del SGC, del censo, etc.)
    geometry: dict                 # GeoJSON (FeatureCollection) o referencia
    visible_for_roles: tuple[str, ...]
    version: str = "1"
    updated_at: datetime = field(default_factory=utcnow)
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida la capa: sin geometría ni roles no se puede dibujar ni proteger."""
        require_text(self.name, "name", max_length=120)
        require_one_of(self.type, LAYER_TYPES, "type")
        require_text(self.source, "source", max_length=200)
        require_text(self.version, "version", max_length=20)
        if not self.geometry:
            raise ValidationError("La capa no tiene geometría que mostrar.")
        if not self.visible_for_roles:
            raise ValidationError("Define qué roles pueden ver la capa.")
        require_unique(list(self.visible_for_roles), "visible_for_roles")
        self.updated_at = require_utc(self.updated_at, "updated_at")

    def is_visible_for(self, role: str) -> bool:
        """True si ese rol puede cargar la capa (CU-10)."""
        return role in self.visible_for_roles

    def publish_new_version(self, geometry: dict, source: str | None = None) -> None:
        """Publica una versión nueva cuando la fuente se actualiza (CU-40)."""
        if not geometry:
            raise ValidationError("La nueva versión no tiene geometría.")
        self.geometry = geometry
        if source:
            require_text(source, "source", max_length=200)
            self.source = source
        major = self.version.split(".")[0]
        self.version = f"{int(major) + 1 if major.isdigit() else 2}.0"
        self.updated_at = utcnow()

    def restrict_to(self, roles: tuple[str, ...]) -> None:
        """Cambia quién puede ver la capa (p. ej. tras una revisión de privacidad)."""
        if not roles:
            raise ValidationError("La capa debe ser visible para al menos un rol.")
        require_unique(list(roles), "visible_for_roles")
        self.visible_for_roles = tuple(roles)
        self.updated_at = utcnow()
