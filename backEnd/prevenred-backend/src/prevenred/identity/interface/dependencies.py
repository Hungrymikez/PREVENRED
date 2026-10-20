"""
Cableado (inyección de dependencias): aquí se "arman" los casos de uso con
sus implementaciones concretas. Es el único lugar que conoce ambos lados.
También contiene la autorización por rol (RBAC, RF-03).
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from prevenred.identity.application.login_user import LoginUser
from prevenred.identity.application.manage_users import ManageUsers
from prevenred.identity.application.ports import PasswordHasher, TokenPayload, TokenService
from prevenred.identity.application.register_user import RegisterUser
from prevenred.identity.application.validate_mfa import RequestMfaCode, VerifyMfaCode
from prevenred.identity.domain.mfa import LOGIN_PURPOSE
from prevenred.identity.domain.repositories import (
    MfaChallengeRepository,
    RoleAssignmentAudit,
    SecondFactorGateway,
    SessionRevoker,
    UserDirectory,
    UserRepository,
)
from prevenred.identity.domain.role import Role
from prevenred.identity.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.identity.infrastructure.jwt_token_service import JwtTokenService
from prevenred.identity.infrastructure.mongo_auth_repository import MongoSessionRepository
from prevenred.identity.infrastructure.mongo_mfa_challenge_repository import (
    MongoMfaChallengeRepository,
)
from prevenred.identity.infrastructure.mongo_role_audit import MongoRoleAssignmentAudit
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.identity.infrastructure.second_factor_gateway import (
    InMemorySecondFactorGateway,
)
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ForbiddenError, UnauthorizedError
from prevenred.shared.infrastructure.config import get_settings
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_db

_bearer = HTTPBearer(auto_error=False)

#: Gateway del segundo factor compartido por TODO el proceso (CU-03).
#:
#: Es UNO solo a propósito: el gateway en memoria recuerda qué código entregó para
#: cada secreto. Si cada petición creara el suyo, el código emitido al iniciar sesión
#: no se podría validar después (cada petición vive en su propia instancia).
#: Al conectar un TOTP/SMS real este singleton desaparece: el código se validaría
#: contra el secreto cifrado de la cuenta, sin estado en el proceso.
_second_factor_gateway: SecondFactorGateway = InMemorySecondFactorGateway()


def get_user_repository(db: Database = Depends(get_db)) -> UserRepository:
    """Entrega el repositorio de usuarios conectado a la base de datos."""
    return MongoUserRepository(db)


def get_hasher() -> PasswordHasher:
    """Entrega el hasher de contraseñas (Argon2)."""
    return Argon2PasswordHasher()


def get_token_service() -> TokenService:
    """Entrega el servicio de tokens configurado con los ajustes de la app."""
    return JwtTokenService(get_settings())


def get_event_bus() -> EventBus:
    """Entrega el bus de eventos compartido."""
    return event_bus


def get_register_user(
    users: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_hasher),
    events: EventBus = Depends(get_event_bus),
) -> RegisterUser:
    """Arma el caso de uso CU-01 con sus dependencias."""
    return RegisterUser(users, hasher, events)


def get_second_factor_gateway() -> SecondFactorGateway:
    """Entrega el gateway del segundo factor (TOTP/SMS/correo) del proceso."""
    return _second_factor_gateway


def get_mfa_challenge_repository(
    db: Database = Depends(get_db),
) -> MfaChallengeRepository:
    """Entrega el repositorio de desafíos del segundo factor (colección `mfa_challenges`)."""
    return MongoMfaChallengeRepository(db)


def get_session_revoker(db: Database = Depends(get_db)) -> SessionRevoker:
    """Entrega el revocador de sesiones (CU-08 A2: al suspender se cierran todas)."""
    return MongoSessionRepository(db)


def get_role_audit(db: Database = Depends(get_db)) -> RoleAssignmentAudit:
    """Entrega la auditoría de cambios de rol y estado (CU-05)."""
    return MongoRoleAssignmentAudit(db)


def get_request_mfa(
    users: UserRepository = Depends(get_user_repository),
    challenges: MfaChallengeRepository = Depends(get_mfa_challenge_repository),
    gateway: SecondFactorGateway = Depends(get_second_factor_gateway),
    events: EventBus = Depends(get_event_bus),
) -> RequestMfaCode:
    """Arma CU-03 paso 1 (pedir el código) con sus dependencias."""
    return RequestMfaCode(users, challenges, gateway, events)


def get_verify_mfa(
    users: UserRepository = Depends(get_user_repository),
    challenges: MfaChallengeRepository = Depends(get_mfa_challenge_repository),
    gateway: SecondFactorGateway = Depends(get_second_factor_gateway),
    events: EventBus = Depends(get_event_bus),
) -> VerifyMfaCode:
    """Arma CU-03 paso 3 (validar el código) con sus dependencias."""
    return VerifyMfaCode(users, challenges, gateway, events)


def get_login_user(
    users: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_hasher),
    tokens: TokenService = Depends(get_token_service),
    request_mfa: RequestMfaCode = Depends(get_request_mfa),
) -> LoginUser:
    """Arma el caso de uso CU-02 con sus dependencias.

    `request_mfa` se cablea aquí (CU-02 A1): cuando la cuenta es administrativa,
    el login no emite token sino que deja abierto el desafío del segundo factor.
    """
    return LoginUser(users, hasher, tokens, request_mfa=request_mfa)


def get_manage_users(
    users: UserDirectory = Depends(get_user_repository),
    challenges: MfaChallengeRepository = Depends(get_mfa_challenge_repository),
    hasher: PasswordHasher = Depends(get_hasher),
    sessions: SessionRevoker = Depends(get_session_revoker),
    audit: RoleAssignmentAudit = Depends(get_role_audit),
    events: EventBus = Depends(get_event_bus),
) -> ManageUsers:
    """Arma CU-08 con sus dependencias.

    `get_user_repository` devuelve `MongoUserRepository`, que ya cumple el contrato
    de `UserDirectory` (E1: nunca quedar sin administradores).
    """
    return ManageUsers(users, challenges, hasher, sessions, audit, events)


def get_current_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    tokens: TokenService = Depends(get_token_service),
) -> TokenPayload:
    """Exige 'Authorization: Bearer <token>' y devuelve quién es y su rol.

    Es la dependencia de las rutas protegidas: NO acepta el token temporal del
    segundo factor. Si llega uno (`scope=mfa`), la cuenta todavía no tiene sesión.
    """
    if creds is None:
        raise UnauthorizedError("Debes iniciar sesión.")
    payload = tokens.decode(creds.credentials)
    if not payload.is_session:
        raise UnauthorizedError(
            "Debes completar la verificación en dos pasos para abrir la sesión."
        )
    return payload


def get_challenge_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    tokens: TokenService = Depends(get_token_service),
) -> TokenPayload:
    """Exige el token TEMPORAL del segundo factor (CU-03 paso 3, `purpose=login`).

    Lo devuelve el login de una cuenta administrativa y solo sirve para validar
    ese código: así nadie con la contraseña de otra cuenta la verifica por ella.
    """
    if creds is None:
        raise UnauthorizedError(
            "Inicia sesión de nuevo para recibir el código de verificación."
        )
    payload = tokens.decode(creds.credentials)
    if not payload.is_mfa_challenge:
        raise UnauthorizedError(
            "Este token no sirve para validar el segundo factor. Inicia sesión de nuevo."
        )
    return payload


def get_mfa_token(
    body: dict | None = None,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    tokens: TokenService = Depends(get_token_service),
) -> TokenPayload:
    """Token aceptado para validar el código, según el `purpose` del cuerpo.

    - `login` (CU-02 A1): exige el token TEMPORAL del segundo factor, que solo
      entrega el login de una cuenta administrativa. Así nadie valida por otro.
    - Cualquier otra operación crítica (p. ej. `admin_users` de CU-08): exige una
      SESIÓN ya abierta. Pedir la contraseña otra vez para confirmar una acción
      debilitaría el paso 1 ("abrir el desafío de la operación"), que supone al
      operador ya dentro; el desafío es de un solo uso y caduca en minutos.

    El cuerpo llega como `dict` genérico porque una dependencia no puede declarar
    el modelo exacto (lo valida el propio endpoint); aquí solo se lee `purpose`.
    """
    if creds is None:
        raise UnauthorizedError("Debes iniciar sesión.")
    purpose = (body or {}).get("purpose") or LOGIN_PURPOSE
    payload = tokens.decode(creds.credentials)
    if purpose == LOGIN_PURPOSE:
        if not payload.is_mfa_challenge:
            raise UnauthorizedError(
                "Este token no sirve para validar el segundo factor. Inicia sesión de nuevo."
            )
    elif not payload.is_session:
        raise UnauthorizedError(
            "Debes iniciar sesión para verificar una operación crítica."
        )
    return payload


def require_roles(*allowed: Role):
    """Fábrica de dependencias RBAC. Uso en otros contextos:
        @router.get("/x", dependencies=[Depends(require_roles(Role.ADMINISTRADOR))])
    Con multirrol basta con tener ALGUNO de los roles permitidos: una cuenta que es
    Técnico y Voluntario entra a las rutas de Técnico y a las de Voluntario.
    Usa `get_current_token`, así que el token del segundo factor tampoco pasa aquí.
    TODO(CU-04): además del rol, validar el modo operacional vigente (RF-03)."""
    def checker(token: TokenPayload = Depends(get_current_token)) -> TokenPayload:
        """Deja pasar si alguno de los roles del token está permitido; si no, responde 403."""
        if not token.has_any_role(*allowed):
            raise ForbiddenError("No tienes permiso para esta función.")
        return token
    return checker
