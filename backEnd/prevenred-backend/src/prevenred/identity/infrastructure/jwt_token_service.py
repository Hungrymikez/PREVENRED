"""Emisión y lectura de tokens JWT de duración limitada (CU-02 paso 4)."""
from datetime import timedelta

import jwt

from prevenred.identity.application.ports import TokenPayload, TokenService
from prevenred.identity.domain.role import Role, highest_privilege_role, normalize_roles
from prevenred.shared.domain.errors import UnauthorizedError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.config import Settings


class JwtTokenService(TokenService):
    """Implementación de TokenService con tokens JWT firmados."""
    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def issue(self, user_id: str, roles: "Role | tuple[Role, ...]") -> str:
        """Crea un JWT con el id del usuario, TODOS sus roles y la fecha de vencimiento."""
        requested = (roles,) if isinstance(roles, Role) else tuple(roles)
        effective = highest_privilege_role(requested)
        now = utcnow()
        claims = {
            "sub": user_id,
            # `role` (singular) se conserva por compatibilidad: es el efectivo.
            "role": effective.value,
            # `roles` (arreglo): todos los de la cuenta, de mayor a menor privilegio.
            "roles": [role.value for role in normalize_roles(requested)],
            "iat": now,
            "exp": now + timedelta(minutes=self._s.jwt_expire_minutes),
        }
        return jwt.encode(claims, self._s.jwt_secret, algorithm=self._s.jwt_algorithm)

    def decode(self, token: str) -> TokenPayload:
        """Valida firma y vencimiento y devuelve el contenido.

        Lanza UnauthorizedError si el token no es válido. Acepta tokens emitidos
        antes de existir el multirrol (solo traen `role`).
        """
        try:
            data = jwt.decode(token, self._s.jwt_secret, algorithms=[self._s.jwt_algorithm])
            raw = data.get("roles") or [data["role"]]
            return TokenPayload(
                user_id=str(data["sub"]), roles=tuple(Role(code) for code in raw)
            )
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            raise UnauthorizedError(
                "Tu sesión no es válida o venció. Inicia sesión de nuevo."
            ) from None
