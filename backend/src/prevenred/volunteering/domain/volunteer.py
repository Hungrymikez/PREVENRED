"""Perfil de voluntario (CU-43). Las reglas viven aquí, no en Mongo."""
from dataclasses import dataclass

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError


@dataclass(kw_only=True, eq=False)
class Volunteer(Entity):
    """Perfil de un voluntario vinculado a una cuenta."""
    user_id: str
    skills: list[str]
    availability: str
    latitude: float
    longitude: float
    authorization_status: str = "PENDIENTE"

    @classmethod
    def register(
        cls,
        *,
        user_id: str,
        skills: list[str],
        availability: str,
        latitude: float,
        longitude: float,
    ) -> "Volunteer":
        """Crea el perfil de voluntario."""
        volunteer = cls(
            user_id=user_id,
            skills=[item.strip() for item in skills if item.strip()],
            availability=availability.strip(),
            latitude=latitude,
            longitude=longitude,
        )
        volunteer._validate()
        return volunteer

    def update_profile(
        self,
        *,
        skills: list[str],
        availability: str,
        latitude: float,
        longitude: float,
    ) -> None:
        """Actualiza habilidades, disponibilidad y ubicación ya validadas."""
        cleaned = [item.strip() for item in skills if item.strip()]
        _check(cleaned, latitude, longitude)
        self.skills = cleaned
        self.availability = availability.strip()
        self.latitude = latitude
        self.longitude = longitude

    def _validate(self) -> None:
        if not self.user_id.strip():
            raise ValidationError("El perfil debe pertenecer a una cuenta.")
        _check(self.skills, self.latitude, self.longitude)


def _check(skills: list[str], latitude: float, longitude: float) -> None:
    if not skills:
        raise ValidationError("Indica al menos una habilidad.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValidationError("La ubicación no es válida.")
