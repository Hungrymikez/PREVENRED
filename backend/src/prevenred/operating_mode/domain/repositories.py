"""Puerto del repositorio de modos operacionales."""

from abc import ABC, abstractmethod

from .mode import OperationalMode


class OperationalModeRepository(ABC):
    """Persistencia del estado operacional vigente y su historial (RN-02)."""

    @abstractmethod
    def get_current_mode(self) -> OperationalMode:
        """Obtiene el estado operacional vigente más reciente."""

    @abstractmethod
    def save(self, mode_record: OperationalMode) -> None:
        """Registra una nueva transición de modo conservando trazabilidad."""
