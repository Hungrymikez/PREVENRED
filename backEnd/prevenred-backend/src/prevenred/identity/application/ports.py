"""Puertos de servicios técnicos que necesitan los casos de uso."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from prevenred.identity.domain.role import Role, highest_privilege_role, normalize_roles


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
    """Datos que viajan dentro del token de sesión: quién es el usuario y sus roles.

    `roles` lleva TODOS los roles de la cuenta (RF-03: multirrol). `role` es el
    efectivo —el de mayor privilegio— y se mantiene por compatibilidad, para que
    el código que ya lee `token.role` siga funcionando sin cambios.
    """
    user_id: str
    roles: tuple[Role, ...]

    def __post_init__(self) -> None:
        """Normaliza los roles: el payload nunca guarda repetidos ni un orden raro."""
        object.__setattr__(self, "roles", normalize_roles(self.roles))

    @property
    def role(self) -> Role:
        """Rol de mayor privilegio del token."""
        return highest_privilege_role(self.roles)

    def has_any_role(self, *allowed: Role) -> bool:
        """True si la cuenta tiene alguno de los roles pedidos (RBAC)."""
        return any(role in self.roles for role in allowed)


class TokenService(ABC):
    """Puerto: emisión y lectura de tokens de sesión."""

    @abstractmethod
    def issue(self, user_id: str, roles: "Role | tuple[Role, ...]") -> str:
        """Emite un token de sesión de duración limitada con TODOS los roles de la cuenta."""

    @abstractmethod
    def decode(self, token: str) -> TokenPayload:
        """Lanza UnauthorizedError si el token es inválido o venció."""
