"""Puerto del repositorio de técnicos. La aplicación no habla con Mongo."""
from abc import ABC, abstractmethod

from prevenred.services.domain.technician import Technician


class TechnicianRepository(ABC):
    """Persistencia del perfil de técnico."""

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Technician | None:
        """Devuelve el perfil de esa cuenta, o None si aún no existe."""

    @abstractmethod
    def add(self, technician: Technician) -> None:
        """Inserta un perfil nuevo."""

    @abstractmethod
    def update(self, technician: Technician) -> None:
        """Guarda el estado que ya validó la entidad."""
