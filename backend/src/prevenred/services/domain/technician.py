"""Perfil profesional del técnico (CU-17). Las reglas viven aquí, no en Mongo."""
from dataclasses import dataclass

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError


@dataclass(kw_only=True, eq=False)
class Technician(Entity):
    """Perfil de un técnico vinculado a una cuenta."""
    user_id: str
    specialties: list[str]
    experience_years: int
    availability: str
    verification_status: str = "PENDIENTE"

    @classmethod
    def register(
        cls,
        *,
        user_id: str,
        specialties: list[str],
        experience_years: int,
        availability: str,
    ) -> "Technician":
        """Crea el perfil en estado Pendiente (CU-17)."""
        technician = cls(
            user_id=user_id,
            specialties=[item.strip() for item in specialties if item.strip()],
            experience_years=experience_years,
            availability=availability.strip(),
        )
        technician._validate()
        return technician

    def update_profile(
        self,
        *,
        specialties: list[str],
        experience_years: int,
        availability: str,
    ) -> None:
        """Actualiza el perfil ya cargado.

        Cambiar especialidad o experiencia reinicia la verificación (CU-17).
        Cambiar solo la disponibilidad no (A1).
        """
        cleaned = [item.strip() for item in specialties if item.strip()]
        _check_profile(cleaned, experience_years)
        verification_changed = (
            cleaned != self.specialties or experience_years != self.experience_years
        )
        self.specialties = cleaned
        self.experience_years = experience_years
        self.availability = availability.strip()
        if verification_changed and self.verification_status == "VERIFICADO":
            self.verification_status = "PENDIENTE"

    def _validate(self) -> None:
        _check_profile(self.specialties, self.experience_years)
        if not self.user_id.strip():
            raise ValidationError("El perfil debe pertenecer a una cuenta.")


def _check_profile(specialties: list[str], experience_years: int) -> None:
    if not specialties:
        raise ValidationError("Indica al menos una especialidad.")
    if experience_years < 0:
        raise ValidationError("Los años de experiencia no pueden ser negativos.")
