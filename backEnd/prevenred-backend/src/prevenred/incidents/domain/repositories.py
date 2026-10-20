"""
Puertos de persistencia de incidentes.

Dos formas de guardar la evidencia de una visita:
  - `update()`: reemplaza con `$set` los campos que controla el dominio.
  - `append_inspection()`: agrega un elemento al arreglo `inspections` con `$push`.
    Se usa `$push` (atómico en un solo documento) para que dos inspectores que
    registran a la vez no se pisen la evidencia; con `$set` del arreglo completo,
    el último en guardar borraría la inspección del otro.
"""
from abc import ABC, abstractmethod

from prevenred.incidents.domain.incident import Incident


class IncidentRepository(ABC):
    """Puerto de persistencia de reportes de emergencia."""

    @abstractmethod
    def get_by_id(self, incident_id: str) -> Incident | None:
        """Busca un reporte por id; None si no existe."""

    @abstractmethod
    def get_by_client_id(self, client_id: str) -> Incident | None:
        """Busca por el id del celular (idempotencia offline, CU-37)."""

    @abstractmethod
    def add(self, incident: Incident) -> None:
        """Guarda un reporte nuevo."""

    @abstractmethod
    def update(self, incident: Incident) -> None:
        """Guarda estado, prioridad, responsable y marca de duplicado."""

    @abstractmethod
    def list_by_reporter(self, user_id: str, *, limit: int = 100) -> list[Incident]:
        """Reportes de una persona (CU-32 'mis casos'), del más reciente al más antiguo."""

    @abstractmethod
    def list_active(self, *, limit: int = 200) -> list[Incident]:
        """Reportes abiertos (sin cerrar) para el tablero, prioridad primero."""

    @abstractmethod
    def list_duplicates_of(self, primary_id: str) -> list[Incident]:
        """Reportes marcados como duplicados de uno principal (CU-30)."""

    @abstractmethod
    def list_nearby(
        self, latitude: float, longitude: float, radius_m: int, *, limit: int = 50
    ) -> list[Incident]:
        """Reportes dentro de un radio en metros: candidatos a duplicado automático."""

    @abstractmethod
    def append_inspection(self, incident_id: str, inspection: dict) -> bool:
        """Agrega una inspección al reporte con `$push`. True si el reporte existía."""
