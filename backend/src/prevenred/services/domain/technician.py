import re
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


class Specialty(StrEnum):
    PLOMERIA = "PLOMERIA"
    ELECTRICIDAD = "ELECTRICIDAD"
    CONSTRUCCION = "CONSTRUCCION"
    CARPINTERIA = "CARPINTERIA"
    PINTURA = "PINTURA"
    CERRAJERIA = "CERRAJERIA"
    OTRO = "OTRO"


class VerificationStatus(StrEnum):
    PENDING = "PENDIENTE"
    VERIFIED = "VERIFICADO"
    REJECTED = "RECHAZADO"


@dataclass
class TechnicianProfile(Entity):
    user_id: EntityId
    full_name: str
    phone_number: str
    specialties: list[Specialty]
    experience_years: int
    bio: str
    verification_status: VerificationStatus
    rating_average: float
    reviews_count: int
    longitude: float
    latitude: float
    created_at: datetime
    verified_by: EntityId | None = None

    @classmethod
    def create(
        cls,
        user_id: EntityId,
        full_name: str,
        phone_number: str,
        specialties: list[Specialty],
        experience_years: int,
        bio: str,
        longitude: float,
        latitude: float,
    ) -> "TechnicianProfile":
        if not full_name or len(full_name.strip()) < 3:
            raise DomainValidationError("El nombre completo debe tener al menos 3 caracteres.")
        clean_phone = re.sub(r"[^\d+]", "", phone_number)
        if len(clean_phone) < 7:
            raise DomainValidationError("Número de teléfono de contacto inválido.")
        if not specialties:
            raise DomainValidationError("Debe especificar al menos una especialidad técnica.")
        if experience_years < 0:
            raise DomainValidationError("Los años de experiencia no pueden ser negativos.")
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise DomainValidationError("Coordenadas geográficas inválidas.")

        return cls(
            id=EntityId.generate(),
            user_id=user_id,
            full_name=full_name.strip(),
            phone_number=clean_phone,
            specialties=specialties,
            experience_years=experience_years,
            bio=bio.strip() if bio else "",
            verification_status=VerificationStatus.PENDING,
            rating_average=0.0,
            reviews_count=0,
            longitude=longitude,
            latitude=latitude,
            created_at=datetime.now(UTC),
            verified_by=None,
        )

    def verify(self, admin_id: EntityId) -> None:
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_by = admin_id

    def reject(self, admin_id: EntityId) -> None:
        self.verification_status = VerificationStatus.REJECTED
        self.verified_by = admin_id

    def generate_whatsapp_link(self, message: str = "") -> str:
        # PrevenRed WhatsApp Deeplink Integration (RF-13, CU-22)
        phone = self.phone_number.replace("+", "")
        base_msg = (
            message.strip()
            or f"Hola {self.full_name}, te contacto desde PrevenRed - OficiosYa Pereira."
        )
        encoded_text = urllib.parse.quote(base_msg)
        return f"https://wa.me/{phone}?text={encoded_text}"
