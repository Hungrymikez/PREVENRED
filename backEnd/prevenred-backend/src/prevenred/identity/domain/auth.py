"""
Sesión (token revocable) y restablecimiento de acceso.

Por qué existen: un JWT no se puede "borrar" del cliente. Para que CU-02 A4
(cerrar sesión) y A2 (recuperar acceso) sean seguros, el servidor guarda en
`sessions` el id único del token (`jti`) y lo marca como revocado; en
`password_resets`, el HASH del enlace temporal (nunca el enlace en claro).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from prevenred.identity.domain.events import SessionRevoked
from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import UnauthorizedError, ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_text, require_utc

# CU-02 A2: vigencia del enlace de recuperación. Provisional hasta definirlo (O-16).
RESET_TTL = timedelta(minutes=30)


@dataclass(kw_only=True, eq=False)
class Session(Entity):
    """Sesión emitida al iniciar sesión: CU-02 A4 la puede revocar."""
    user_id: str
    jti: str                       # id único del token (claim `jti` del JWT)
    expires_at: datetime
    revoked_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        """True si la sesión no está revocada y aún no vence (CU-02 A3/A4)."""
        return self.revoked_at is None and now < self.expires_at

    def require_valid(self, now: datetime) -> None:
        """Lanza UnauthorizedError si la sesión ya no sirve (revocada o vencida)."""
        if not self.is_valid(now):
            raise UnauthorizedError("Tu sesión terminó. Vuelve a iniciar sesión.")

    def revoke(self) -> None:
        """CU-02 A4: cierra sesión. Revocar dos veces no es error (idempotente)."""
        if self.revoked_at is not None:
            return
        self.revoked_at = utcnow()
        self.record_event(SessionRevoked(user_id=self.user_id, jti=self.jti))


@dataclass(kw_only=True, eq=False)
class PasswordReset(Entity):
    """Enlace temporal de recuperación de acceso (CU-02 A2).

    Se guarda el SHA-256 del token, no el token: si alguien lee la base, no puede
    usar el enlace. El token en claro solo viaja en el correo/SMS.
    """
    user_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None

    def is_usable(self, now: datetime) -> bool:
        """True si el enlace no se usó y no ha vencido (un enlace sirve UNA sola vez)."""
        return self.used_at is None and now < self.expires_at

    def require_usable(self, now: datetime) -> None:
        """Lanza ValidationError con mensaje accionable si el enlace ya no sirve."""
        if self.used_at is not None:
            raise ValidationError("Ese enlace de recuperación ya se usó. Solicita uno nuevo.")
        if now >= self.expires_at:
            raise ValidationError("El enlace de recuperación venció. Solicita uno nuevo.")

    def mark_used(self, now: datetime) -> None:
        """Marca el enlace como consumido (no se puede reutilizar)."""
        self.require_usable(now)
        self.used_at = require_utc(now, "used_at")

    @classmethod
    def issue(
        cls, *, user_id: str, token_hash: str, now: datetime | None = None
    ) -> "PasswordReset":
        """Crea el registro del enlace con su vencimiento (CU-02 A2)."""
        require_text(user_id, "user_id", max_length=64)
        require_text(token_hash, "token_hash", max_length=128)
        issued = now or utcnow()
        return cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=issued + RESET_TTL,
            created_at=require_utc(issued, "created_at"),
        )
