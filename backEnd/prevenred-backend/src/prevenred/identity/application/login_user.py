"""
CU-02 · Iniciar sesión.
Seguridad: ante credenciales malas siempre el mismo mensaje genérico (E1) para
no revelar si el correo existe.
"""
from dataclasses import dataclass

from prevenred.identity.application.ports import PasswordHasher, TokenService
from prevenred.identity.application.validate_mfa import RequestMfaCode, RequestMfaCommand
from prevenred.identity.domain.mfa import LOGIN_PURPOSE
from prevenred.identity.domain.repositories import UserRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.value_objects import Email
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
    """Resultado de un inicio de sesión: el token (si ya se puede) y el rol.

    Una cuenta administrativa recibe `access_token=None` y `mfa_required=True`:
    la contraseña fue correcta, pero NO hay sesión hasta validar el segundo factor
    (CU-03). Así el cliente sabe que debe pedir el código, sin recibir un token a
    medias que pudiera usarse sin MFA.
    """
    access_token: str | None
    role: Role
    mfa_required: bool = False
    # TODO(CU-04): incluir el modo operacional vigente (Cotidiano/Emergencia).


class LoginUser:
    """Caso de uso CU-02: valida credenciales, aplica el bloqueo por intentos y emite el token."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        request_mfa: RequestMfaCode | None = None,
    ) -> None:
        """`request_mfa` es opcional para no romper pruebas puras del login;
        cuando falta, una cuenta administrativa falla cerrado (no hay sesión)."""
        self._users, self._hasher, self._tokens = users, hasher, tokens
        self._request_mfa = request_mfa

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

        # CU-02 A1 / RN-07: la cuenta administrativa NO recibe sesión todavía.
        # La contraseña sola no basta: se pide el segundo factor (CU-03) y solo
        # después de validarlo se emite el token.
        if user.role.is_administrative:
            if self._request_mfa is not None:
                self._request_mfa.execute(
                    RequestMfaCommand(user_id=user.id, purpose=LOGIN_PURPOSE)
                )
            return AuthResult(access_token=None, role=user.role, mfa_required=True)

        user.register_successful_login()
        self._users.update(user)
        return AuthResult(access_token=self._tokens.issue(user.id, user.roles), role=user.role)
