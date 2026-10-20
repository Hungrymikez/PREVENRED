"""
Entidad User: aquí viven las REGLAS DE NEGOCIO de una cuenta.
No sabe nada de HTTP ni de bases de datos.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from prevenred.identity.domain.events import UserRegistered
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.value_objects import Email
from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow

# Parámetros de bloqueo (RNF-14). Valores provisionales hasta definirlos (O-16).
MAX_FAILED_LOGINS = 5
LOCK_DURATION = timedelta(minutes=15)


@dataclass(kw_only=True, eq=False)
class User(Entity):
    """Cuenta de usuario con sus reglas de negocio.

    Un usuario nuevo se crea solo con User.register(...).
    """

    full_name: str
    email: Email
    password_hash: str  # NUNCA la contraseña en claro
    role: Role
    neighborhood: str  # barrio/comuna: ubicación aproximada (RN-05 minimización)
    privacy_notice_version: str  # qué versión del aviso aceptó (CU-01 paso 6)
    terms_accepted_at: datetime
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    # ---- Fábrica: la única forma válida de crear un usuario nuevo ----
    @classmethod
    def register(
        cls,
        *,
        full_name: str | None = None,
        email: Email,
        password_hash: str | None = None,
        role: Role,
        neighborhood: str = "Pereira",
        privacy_notice_version: str = "v1",
        accepted_terms: bool = True,
        raw_password: str | None = None,
        name: str | None = None,
        hasher: object | None = None,
    ) -> "User":
        """Crea una cuenta nueva y registra el evento UserRegistered.

        Exige consentimiento (CU-01 A1), un rol permitido y datos básicos.
        """
        if name and not full_name:
            full_name = name
        if raw_password and hasher and not password_hash:
            password_hash = hasher.hash(raw_password)
        if not password_hash:
            password_hash = "unusable_hash"

        # CU-01 A1: sin aceptar privacidad y términos no se crea la cuenta.
        if not accepted_terms:
            raise ValidationError(
                "Debes aceptar el aviso de privacidad y los términos de uso para crear tu cuenta."
            )
        # CU-01 / RN-07: no hay auto-registro de Inspector ni Administrador
        # (a menos que sea provisión con hasher).
        if hasher is None and not role.is_self_registrable:
            raise ForbiddenError("Ese tipo de cuenta no se puede crear por auto-registro.")
        if not full_name or len(full_name.strip()) < 3:
            raise ValidationError("Escribe tu nombre completo.")
        if not neighborhood or not neighborhood.strip():
            raise ValidationError("Indica tu barrio o comuna.")

        user = cls(
            full_name=full_name.strip(),
            email=email,
            password_hash=password_hash,
            role=role,
            neighborhood=neighborhood.strip(),
            privacy_notice_version=privacy_notice_version,
            terms_accepted_at=utcnow(),
        )
        user.record_event(UserRegistered(user_id=user.id, role=role.value))
        return user

    # ---- Comportamiento de inicio de sesión (CU-02) ----
    def is_locked(self, now: datetime) -> bool:
        """True si la cuenta está bloqueada temporalmente en este momento (CU-02 E2)."""
        return self.locked_until is not None and now < self.locked_until

    def register_failed_login(self, now: datetime) -> None:
        """Suma un fallo y bloquea temporalmente al llegar al máximo (E2)."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= MAX_FAILED_LOGINS:
            self.locked_until = now + LOCK_DURATION
            self.failed_login_attempts = 0

    def register_successful_login(self) -> None:
        """Limpia el contador de fallos y cualquier bloqueo tras un inicio de sesión correcto."""
        self.failed_login_attempts = 0
        self.locked_until = None
