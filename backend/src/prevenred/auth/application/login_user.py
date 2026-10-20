"""
CU-02 · Iniciar sesión.
Seguridad: ante credenciales malas siempre el mismo mensaje genérico (E1) para
no revelar si el correo existe.
"""
from dataclasses import dataclass

from prevenred.auth.application.ports import PasswordHasher, TokenService
from prevenred.auth.domain.repositories import UserRepository
from prevenred.auth.domain.role import Role
from prevenred.auth.domain.value_objects import Email
from prevenred.shared.domain.errors import (
    ForbiddenError,
    TooManyAttemptsError,
    UnauthorizedError,
    ValidationError,
)
from prevenred.shared.domain.events import utcnow

_GENERIC = "Correo o contraseña incorrectos."


@dataclass(frozen=True)
class LoginCommand:
    """Datos de entrada del caso de uso CU-02."""
    email: str
    password: str


@dataclass(frozen=True)
class AuthResult:
    """Resultado de un inicio de sesión exitoso: el token y el rol del usuario."""
    access_token: str
    role: Role
    # TODO(CU-04): incluir el modo operacional vigente (Cotidiano/Emergencia).


class LoginUser:
    """Caso de uso CU-02: valida credenciales, aplica el bloqueo por intentos y emite el token."""
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        *,
        mfa_required: bool = True,
    ) -> None:
        self._users, self._hasher, self._tokens = users, hasher, tokens
        # Por defecto fallamos cerrado. Solo el cableado lo apaga en development
        # o cuando MFA_ENABLED=false (CU-03 aún no tiene el segundo factor).
        self._mfa_required = mfa_required

    def execute(self, cmd: LoginCommand) -> AuthResult:
        """Inicia sesión.

        Lanza UnauthorizedError, TooManyAttemptsError o ForbiddenError (E1-E3, A1).
        """
        try:
            email = Email(cmd.email)
        except ValidationError:
            # No distinguimos "formato malo" de "no existe" (no revelar si el correo existe).
            raise UnauthorizedError(_GENERIC) from None

        user = self._users.get_by_email(email)
        if user is None:
            raise UnauthorizedError(_GENERIC)

        now = utcnow()
        if user.is_locked(now):                              # E2
            raise TooManyAttemptsError("Demasiados intentos. Intenta de nuevo más tarde.")
        if not user.is_active:                               # E3
            raise ForbiddenError("Tu cuenta está desactivada. Comunícate con la entidad.")

        if not self._hasher.verify(cmd.password, user.password_hash):
            user.register_failed_login(now)
            self._users.update(user)    # se guarda el fallo ANTES de lanzar el error
            raise UnauthorizedError(_GENERIC)

        # A1 / RN-07: cuentas administrativas exigen MFA (CU-03). Mientras CU-03 no
        # esté implementado, NO se emite sesión, salvo bypass explícito de desarrollo.
        if user.role.is_administrative and self._mfa_required:
            raise ForbiddenError("Las cuentas administrativas requieren verificación en dos pasos.")

        user.register_successful_login()
        self._users.update(user)
        return AuthResult(access_token=self._tokens.issue(user.id, user.role), role=user.role)
