"""Puertos de servicios técnicos que necesitan los casos de uso."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from prevenred.identity.domain.role import Role


class PasswordHasher(ABC):
    """Puerto: cómo se protegen y comparan las contraseñas.

    Cada implementación elige el algoritmo.
    """

    @abstractmethod
    def hash(self, plain: str) -> str:
        """Devuelve el hash seguro de una contraseña en claro."""

    @abstractmethod
    def verify(self, plain: str, hashed: str) -> bool:
        """True si la contraseña en claro corresponde al hash guardado."""


@dataclass(frozen=True)
class TokenPayload:
    """Datos que viajan dentro del token de sesión: quién es el usuario y qué rol tiene."""

    user_id: str
    role: Role


class TokenService(ABC):
    """Puerto: emisión y lectura de tokens de sesión."""

    @abstractmethod
    def issue(self, user_id: str, role: Role) -> str:
        """Emite un token de sesión de duración limitada para el usuario."""

    @abstractmethod
    def decode(self, token: str) -> TokenPayload:
        """Lanza UnauthorizedError si el token es inválido o venció."""
