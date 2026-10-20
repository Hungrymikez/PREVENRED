"""Emisión y lectura de tokens JWT de duración limitada (CU-02 paso 4)."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from prevenred.identity.application.ports import TokenPayload, TokenService
from prevenred.identity.domain.role import Role
from prevenred.shared.domain.errors import UnauthorizedError
from prevenred.shared.infrastructure.config import Settings


class JwtTokenService(TokenService):
    """Implementación de TokenService con tokens JWT firmados."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def issue(self, user_id: str, role: Role) -> str:
        """Crea un JWT con el id del usuario, su rol y la fecha de vencimiento.

        Calcula dinámicamente el tiempo actual (iat) y la expiración (exp) en
        timezone-aware UTC en cada llamada, incorporando jti para garantizar unicidad.
        """
        now = datetime.now(UTC)
        claims = {
            "sub": user_id,
            "role": role.value,
            "iat": now,
            "exp": now + timedelta(minutes=self._s.jwt_expire_minutes),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(claims, self._s.jwt_secret, algorithm=self._s.jwt_algorithm)

    def decode(self, token: str) -> TokenPayload:
        """Valida firma y vencimiento y devuelve el contenido.

        Lanza UnauthorizedError si el token no es válido o ha expirado.
        """
        try:
            data = jwt.decode(
                token,
                self._s.jwt_secret,
                algorithms=[self._s.jwt_algorithm],
                options={"verify_exp": True, "verify_iat": True},
            )
            return TokenPayload(user_id=str(data["sub"]), role=Role(data["role"]))
        except (jwt.PyJWTError, KeyError, ValueError):
            raise UnauthorizedError(
                "Tu sesión no es válida o venció. Inicia sesión de nuevo."
            ) from None
