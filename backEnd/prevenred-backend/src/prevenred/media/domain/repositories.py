"""
Puerto de persistencia de archivos (media). El dominio dice QUÉ necesita.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from prevenred.media.domain.file import StoredFile


class FileRepository(ABC):
    """Puerto de metadatos de archivos (CU-47)."""

    @abstractmethod
    def get_by_id(self, file_id: str) -> StoredFile | None:
        """Busca un archivo por id; None si no existe."""

    @abstractmethod
    def add(self, file: StoredFile) -> None:
        """Registra los metadatos de un archivo ya subido al almacenamiento."""

    @abstractmethod
    def update(self, file: StoredFile) -> None:
        """Guarda cambios (p. ej. vincular a un reporte o retirar acceso)."""

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """Borra los metadatos. True si existía (RN-06: retención)."""

    @abstractmethod
    def list_by_owner(self, owner_id: str, *, limit: int = 50) -> list[StoredFile]:
        """Archivos de una persona, del más reciente al más antiguo."""

    @abstractmethod
    def list_by_link(self, collection: str, target_id: str) -> list[StoredFile]:
        """Archivos vinculados a un documento (p. ej. las fotos de un reporte)."""

    @abstractmethod
    def list_expired(self, now: datetime, *, limit: int = 200) -> list[StoredFile]:
        """Archivos que ya cumplieron su retención y deben eliminarse (RN-06)."""
