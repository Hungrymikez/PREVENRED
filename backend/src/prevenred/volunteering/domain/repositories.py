"""Puerto del repositorio de voluntarios."""
from abc import ABC, abstractmethod

from prevenred.volunteering.domain.volunteer import Volunteer


class VolunteerRepository(ABC):
    """Persistencia del perfil de voluntario."""

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Volunteer | None:
        """Devuelve el perfil de esa cuenta, o None si aún no existe."""

    @abstractmethod
    def add(self, volunteer: Volunteer) -> None:
        """Inserta un perfil nuevo."""

    @abstractmethod
    def update(self, volunteer: Volunteer) -> None:
        """Guarda el estado que ya validó la entidad."""
