"""
Entidad File (metadatos de un archivo) — colección `files`, CU-47.

Por qué existe: las fotos, videos y documentos de los reportes NO se sirven con
URL pública. Se guarda la referencia segura (`url`) y quién puede verla
(`access_roles`, RN-06), para que la descarga pase siempre por el servidor y
quede registrada. La fecha de retención permite borrar lo que ya no debe
conservarse (RN-06 / RN-03).
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

#: Límites de tamaño por tipo de archivo (provisional hasta definir RNF de cuota).
MAX_IMAGE_BYTES = 10 * 1024 * 1024        # 10 MB
MAX_VIDEO_BYTES = 50 * 1024 * 1024        # 50 MB
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024      # 5 MB

#: Tipos aceptados. Se valida aquí porque aceptar cualquier MIME permitiría
#: subir ejecutables o scripts disfrazados de foto.
IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/heic")
VIDEO_TYPES = ("video/mp4", "video/quicktime")
DOCUMENT_TYPES = ("application/pdf",)


@dataclass(kw_only=True, eq=False)
class StoredFile(Entity):
    """Archivo almacenado con acceso restringido.

    `StoredFile` y no `File` para no confundirla con `pathlib`/tipos del sistema.
    """
    owner_id: str
    file_name: str
    mime_type: str
    url: str                       # referencia segura, no una URL pública
    size: int
    category: str                  # FOTO / VIDEO / DOCUMENTO / PORTFOLIO...
    access_roles: tuple[str, ...]  # códigos de rol que pueden verlo (RN-06)
    linked_collection: str | None = None   # a qué colección pertenece
    linked_id: str | None = None
    encrypted: bool = True         # RNF-05: cifrado en reposo
    retention_until: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida el archivo al crearlo o al reconstruirlo (G3, RN-06)."""
        require_text(self.owner_id, "owner_id", max_length=64)
        require_text(self.file_name, "file_name", max_length=255)
        require_text(self.category, "category", max_length=40)
        require_text(self.url, "url", max_length=2000)
        require_unique(list(self.access_roles), "access_roles")
        if not self.access_roles:
            raise ValidationError("Define qué roles pueden ver el archivo.")
        if self.size <= 0:
            raise ValidationError("El archivo está vacío.")
        self.validate_type_and_size()
        if self.retention_until is not None:
            self.retention_until = require_utc(self.retention_until, "retention_until")

    def validate_type_and_size(self) -> None:
        """Rechaza archivos que no son imagen, video ni PDF, o que excedan el límite."""
        if self.mime_type in IMAGE_TYPES:
            limit = MAX_IMAGE_BYTES
        elif self.mime_type in VIDEO_TYPES:
            limit = MAX_VIDEO_BYTES
        elif self.mime_type in DOCUMENT_TYPES:
            limit = MAX_DOCUMENT_BYTES
        else:
            require_one_of(self.mime_type, IMAGE_TYPES + VIDEO_TYPES + DOCUMENT_TYPES, "mime_type")
            return
        if self.size > limit:
            raise ValidationError(
                f"El archivo supera el tamaño permitido ({limit // (1024 * 1024)} MB)."
            )

    def link_to(self, collection: str, target_id: str) -> None:
        """Asocia el archivo a un reporte/inmueble/necesidad (CU-47)."""
        require_text(collection, "linked_collection", max_length=60)
        require_text(target_id, "linked_id", max_length=64)
        self.linked_collection = collection
        self.linked_id = target_id

    def can_be_seen_by(self, role: str) -> bool:
        """True si ese rol puede descargarlo (RN-06)."""
        return role in self.access_roles

    def is_expired(self, now: datetime) -> bool:
        """True si ya pasó su fecha de retención y debe eliminarse (RN-06)."""
        return self.retention_until is not None and now >= self.retention_until
