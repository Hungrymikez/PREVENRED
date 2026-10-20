"""
Entidades de servicios: `TechnicianProfile` (CU-17, CU-18, CU-19, CU-44).

Por qué una entidad separada de `User`: la verificación profesional es un
proceso con documentos, revisor y fechas, y no debe mezclarse con la cuenta.
Un técnico sin verificar puede tener perfil y recibir solicitudes, pero no
aparece como `VERIFICADO` en las búsquedas (CU-19).
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import (
    require_between,
    require_one_of,
    require_text,
    require_unique,
    require_utc,
)

#: Estados de verificación del técnico (CU-17/CU-18).
VERIFICATION_STATUSES = ("PENDIENTE", "VERIFICADO", "RECHAZADO")


@dataclass(kw_only=True, eq=False)
class TechnicianProfile(Entity):
    """Perfil profesional de un técnico o voluntario con oficio (CU-17)."""
    user_id: str
    specialties: tuple[str, ...]
    experience_years: int = 0
    verification_status: str = "PENDIENTE"
    portfolio: tuple[str, ...] = ()       # ids de files (CU-47)
    documents: tuple[str, ...] = ()       # soportes de verificación (CU-17)
    availability: dict = field(default_factory=dict)
    rating: float = 0.0
    verified_by: str | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Valida especialidades, experiencia y coherencia de la verificación."""
        require_text(self.user_id, "user_id", max_length=64)
        if not self.specialties:
            raise ValidationError("El técnico debe tener al menos una especialidad.")
        for speciality in self.specialties:
            require_text(speciality, "specialties", max_length=60)
        require_unique(list(self.specialties), "specialties")
        require_between(self.experience_years, 0, 70, "experience_years")
        require_between(self.rating, 0, 5, "rating")
        require_one_of(self.verification_status, VERIFICATION_STATUSES, "verification_status")
        if self.verified_at is not None:
            self.verified_at = require_utc(self.verified_at, "verified_at")
        if self.updated_at is not None:
            self.updated_at = require_utc(self.updated_at, "updated_at")
        if self.verification_status == "VERIFICADO" and not self.verified_by:
            raise ValidationError("Una verificación debe registrar quién la aprobó.")

    @property
    def verified(self) -> bool:
        """True si el administrador ya aprobó los documentos."""
        return self.verification_status == "VERIFICADO"

    def attach_documents(self, document_ids: tuple[str, ...]) -> None:
        """Agrega soportes y devuelve el perfil a `PENDIENTE` (CU-17).

        Subir documentos nuevos invalida una verificación previa: de lo
        contrario se aprobaría al técnico sin haber leído lo entregado.
        """
        if not document_ids:
            raise ValidationError("Debes adjuntar al menos un documento.")
        self.documents = tuple(dict.fromkeys((*self.documents, *document_ids)))
        self.verification_status = "PENDIENTE"
        self.rejection_reason = None
        self.verified_by = None
        self.verified_at = None
        self.updated_at = utcnow()

    def verify(self, admin_id: str, at: datetime | None = None) -> None:
        """El administrador aprueba el perfil (CU-18)."""
        require_text(admin_id, "admin_id", max_length=64)
        if self.verified:
            raise ValidationError("Este técnico ya está verificado.")
        if not self.documents:
            raise ValidationError("No se puede verificar un perfil sin documentos.")
        self.verification_status = "VERIFICADO"
        self.verified_by = admin_id
        self.verified_at = require_utc(at or utcnow(), "verified_at")
        self.rejection_reason = None
        self.updated_at = self.verified_at

    def reject(self, admin_id: str, reason: str, at: datetime | None = None) -> None:
        """El administrador rechaza el perfil indicando el motivo (CU-18)."""
        require_text(admin_id, "admin_id", max_length=64)
        require_text(reason, "reason", max_length=500)
        self.verification_status = "RECHAZADO"
        self.verified_by = admin_id
        self.verified_at = require_utc(at or utcnow(), "verified_at")
        self.rejection_reason = reason
        self.updated_at = self.verified_at
