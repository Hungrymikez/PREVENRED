"""
Puerto (interfaz) del repositorio. El dominio dice QUÉ necesita guardar/leer;
la capa infrastructure decide CÓMO (PyMongo, memoria para tests, etc.).
"""
from abc import ABC, abstractmethod

from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email


class UserRepository(ABC):
    """Puerto de persistencia de usuarios (lo implementa la capa infrastructure)."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        """Busca un usuario por su id; devuelve None si no existe."""

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        """Busca un usuario por su correo ya normalizado; devuelve None si no existe."""

    @abstractmethod
    def add(self, user: User) -> None:
        """Guarda un usuario nuevo. Lanza ConflictError si el correo ya existe."""

    @abstractmethod
    def update(self, user: User) -> None:
        """Guarda los cambios de un usuario existente."""
