"""
Cableado (inyección de dependencias): aquí se "arman" los casos de uso con
sus implementaciones concretas. Es el único lugar que conoce ambos lados.
También contiene la autorización por rol (RBAC, RF-03).
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from prevenred.auth.application.login_user import LoginUser
from prevenred.auth.application.ports import PasswordHasher, TokenPayload, TokenService
from prevenred.auth.application.register_user import RegisterUser
from prevenred.auth.domain.repositories import UserRepository
from prevenred.auth.domain.role import Role
from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.auth.infrastructure.jwt_token_service import JwtTokenService
from prevenred.auth.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ForbiddenError, UnauthorizedError
from prevenred.shared.infrastructure.config import get_settings
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_db

_bearer = HTTPBearer(auto_error=False)


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


def get_login_user(
    users: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_hasher),
    tokens: TokenService = Depends(get_token_service),
) -> LoginUser:
    """Arma el caso de uso CU-02 con sus dependencias."""
    settings = get_settings()
    return LoginUser(
        users,
        hasher,
        tokens,
        mfa_required=settings.admin_login_requires_mfa,
    )


def get_current_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    tokens: TokenService = Depends(get_token_service),
) -> TokenPayload:
    """Exige 'Authorization: Bearer <token>' y devuelve quién es y su rol."""
    if creds is None:
        raise UnauthorizedError("Debes iniciar sesión.")
    return tokens.decode(creds.credentials)


def require_roles(*allowed: Role):
    """Fábrica de dependencias RBAC. Uso en otros contextos:
        @router.get("/x", dependencies=[Depends(require_roles(Role.ADMINISTRADOR))])
    TODO(CU-04): además del rol, validar el modo operacional vigente (RF-03)."""
    def checker(token: TokenPayload = Depends(get_current_token)) -> TokenPayload:
        """Deja pasar solo si el rol del token está entre los permitidos; si no, responde 403."""
        if token.role not in allowed:
            raise ForbiddenError("No tienes permiso para esta función.")
        return token
    return checker
