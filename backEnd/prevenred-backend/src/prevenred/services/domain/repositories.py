"""
Puertos de servicios (CU-17, CU-18, CU-19, CU-44).

`list_verification_queue` es el "pendientes" del panel administrativo; se separa
de `search` porque la cola incluye perfiles NO verificados, mientras que la
búsqueda pública solo devuelve aprobados.
"""
from abc import ABC, abstractmethod

from prevenred.services.domain.entities import TechnicianProfile


class TechnicianRepository(ABC):
    """Puerto de los perfiles de técnico."""

    @abstractmethod
    def get_by_id(self, profile_id: str) -> TechnicianProfile | None:
        """Busca un perfil por id."""

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> TechnicianProfile | None:
        """Perfil del usuario (uno por persona)."""

    @abstractmethod
    def add(self, profile: TechnicianProfile) -> None:
        """Registra el perfil al completar el onboarding (CU-17)."""

    @abstractmethod
    def update(self, profile: TechnicianProfile) -> None:
        """Guarda documentos, verificación y disponibilidad."""

    @abstractmethod
    def search(
        self,
        *,
        specialty: str | None = None,
        verified_only: bool = True,
        limit: int = 50,
    ) -> list[TechnicianProfile]:
        """Técnicos para un oficio; los mejor valorados primero (CU-19)."""

    @abstractmethod
    def list_verification_queue(self, *, limit: int = 100) -> list[TechnicianProfile]:
        """Perfiles pendientes de revisión, del más antiguo al más nuevo (CU-18)."""
