"""Puertos de servicios técnicos que necesitan los casos de uso."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from prevenred.identity.domain.role import Role, highest_privilege_role, normalize_roles

#: Alcance del token de SESIÓN: el que usan todas las rutas protegidas.
SESSION_SCOPE = "session"

#: Alcance del token TEMPORAL del segundo factor (CU-03 paso 3): prueba que la
#: contraseña fue correcta y solo sirve para validar el código. No abre sesión.
MFA_SCOPE = "mfa"


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

    `scope` distingue una SESIÓN (`session`, la de siempre) del token temporal que
    se entrega al iniciar sesión una cuenta administrativa (`mfa`): ese último solo
    sirve para validar el segundo factor, nunca para operar. Se llama `scope` y no
    `scopes` a propósito, para no confundirlo con el alcance OAuth2 de FastAPI.
    """
    user_id: str
    roles: tuple[Role, ...]
    scope: str = SESSION_SCOPE

    def __post_init__(self) -> None:
        """Normaliza los roles: el payload nunca guarda repetidos ni un orden raro."""
        object.__setattr__(self, "roles", normalize_roles(self.roles))

    @property
    def role(self) -> Role:
        """Rol de mayor privilegio del token."""
        return highest_privilege_role(self.roles)

    @property
    def is_session(self) -> bool:
        """True si es un token de sesión (el que usan las rutas protegidas)."""
        return self.scope == SESSION_SCOPE

    @property
    def is_mfa_challenge(self) -> bool:
        """True si es el token temporal del segundo factor (CU-03 paso 3)."""
        return self.scope == MFA_SCOPE

    def has_any_role(self, *allowed: Role) -> bool:
        """True si la cuenta tiene alguno de los roles pedidos (RBAC)."""
        return any(role in self.roles for role in allowed)


class TokenService(ABC):
    """Puerto: emisión y lectura de tokens de sesión."""

    @abstractmethod
    def issue(self, user_id: str, roles: "Role | tuple[Role, ...]") -> str:
        """Emite un token de sesión de duración limitada con TODOS los roles de la cuenta."""

    @abstractmethod
    def issue_mfa_challenge(
        self, user_id: str, roles: "Role | tuple[Role, ...]"
    ) -> str:
        """Emite el token TEMPORAL del segundo factor (CU-03 paso 3).

        Prueba que la contraseña fue correcta para poder validar el código; NO abre
        sesión. Dura minutos y solo lo acepta la ruta de validación del código.
        """

    @abstractmethod
    def decode(self, token: str) -> TokenPayload:
        """Lanza UnauthorizedError si el token es inválido o venció."""
