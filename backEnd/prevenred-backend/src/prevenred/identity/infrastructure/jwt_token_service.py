"""Emisión y lectura de tokens JWT de duración limitada (CU-02 paso 4)."""
from datetime import datetime, timedelta

import jwt

from prevenred.identity.application.ports import (
    MFA_SCOPE,
    SESSION_SCOPE,
    TokenPayload,
    TokenService,
)
from prevenred.identity.domain.role import Role, highest_privilege_role, normalize_roles
from prevenred.shared.domain.errors import UnauthorizedError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.config import Settings

#: Minutos de vida del token del segundo factor (CU-03 paso 3). Es corto a
#: propósito: solo cubre poner el código, que vence a los 5 minutos
#: (`CODE_TTL`); si se vence, se vuelve a iniciar sesión. Provisional (O-16).
MFA_TOKEN_MINUTES = 10


class JwtTokenService(TokenService):
    """Implementación de TokenService con tokens JWT firmados."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def issue(self, user_id: str, roles: "Role | tuple[Role, ...]") -> str:
        """Crea un JWT de SESIÓN con el id del usuario, TODOS sus roles y el vencimiento."""
        return self._encode(
            user_id, roles, scope=SESSION_SCOPE,
            expires_at=utcnow() + timedelta(minutes=self._s.jwt_expire_minutes),
        )

    def issue_mfa_challenge(self, user_id: str, roles: "Role | tuple[Role, ...]") -> str:
        """Crea el JWT TEMPORAL del segundo factor (no abre sesión: `scope=mfa`)."""
        return self._encode(
            user_id, roles, scope=MFA_SCOPE,
            expires_at=utcnow() + timedelta(minutes=MFA_TOKEN_MINUTES),
        )

    def _encode(
        self,
        user_id: str,
        roles: "Role | tuple[Role, ...]",
        *,
        scope: str,
        expires_at: datetime,
    ) -> str:
        """Firma el token con los roles, el alcance y el vencimiento indicados."""
        requested = (roles,) if isinstance(roles, Role) else tuple(roles)
        effective = highest_privilege_role(requested)
        claims = {
            "sub": user_id,
            # `role` (singular) se conserva por compatibilidad: es el efectivo.
            "role": effective.value,
            # `roles` (arreglo): todos los de la cuenta, de mayor a menor privilegio.
            "roles": [role.value for role in normalize_roles(requested)],
            # `scope` separa la sesión del token temporal del segundo factor.
            "scope": scope,
            "iat": utcnow(),
            "exp": expires_at,
        }
        return jwt.encode(claims, self._s.jwt_secret, algorithm=self._s.jwt_algorithm)

    def decode(self, token: str) -> TokenPayload:
        """Valida firma y vencimiento y devuelve el contenido.

        Lanza UnauthorizedError si el token no es válido. Acepta tokens emitidos
        antes de existir el multirrol (solo traen `role`) y de que existiera el
        `scope`: esos tokens son de sesión.
        """
        try:
            data = jwt.decode(token, self._s.jwt_secret, algorithms=[self._s.jwt_algorithm])
            raw = data.get("roles") or [data["role"]]
            return TokenPayload(
                user_id=str(data["sub"]),
                roles=tuple(Role(code) for code in raw),
                scope=str(data.get("scope", SESSION_SCOPE)),
            )
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            raise UnauthorizedError(
                "Tu sesión no es válida o venció. Inicia sesión de nuevo."
            ) from None

