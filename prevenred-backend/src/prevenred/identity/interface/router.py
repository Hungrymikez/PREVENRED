"""Rutas HTTP del contexto identity. Solo traducen HTTP <-> casos de uso."""

from fastapi import APIRouter, Depends

from prevenred.identity.application.login_user import LoginCommand, LoginUser
from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.application.register_user import RegisterUser, RegisterUserCommand
from prevenred.identity.domain.repositories import UserRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.interface.dependencies import (
    get_current_token,
    get_login_user,
    get_register_user,
    get_user_repository,
)
from prevenred.identity.interface.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from prevenred.shared.domain.errors import NotFoundError

router = APIRouter(prefix="/api/v1/auth", tags=["Acceso (M01)"])


@router.post("/register", response_model=UserResponse, status_code=201, summary="CU-01 Registrarse")
def register(body: RegisterRequest, use_case: RegisterUser = Depends(get_register_user)):
    """CU-01: crea una cuenta y devuelve sus datos públicos (nunca la contraseña)."""
    user = use_case.execute(
        RegisterUserCommand(
            full_name=body.full_name,
            email=body.email,
            password=body.password,
            role=Role(body.role),
            neighborhood=body.neighborhood,
            privacy_notice_version=body.privacy_notice_version,
            accepted_terms=body.accepted_terms,
        )
    )
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email.value,
        role=user.role.value,
        neighborhood=user.neighborhood,
    )


@router.post("/login", response_model=TokenResponse, summary="CU-02 Iniciar sesión")
def login(body: LoginRequest, use_case: LoginUser = Depends(get_login_user)):
    """CU-02: valida las credenciales y devuelve el token de sesión."""
    result = use_case.execute(LoginCommand(email=body.email, password=body.password))
    return TokenResponse(access_token=result.access_token, role=result.role.value)


@router.get("/me", response_model=UserResponse, summary="Usuario de la sesión actual")
def me(
    token: TokenPayload = Depends(get_current_token),
    users: UserRepository = Depends(get_user_repository),
):
    """Devuelve los datos de la cuenta dueña del token."""
    user = users.get_by_id(token.user_id)
    if user is None:
        raise NotFoundError("La cuenta ya no existe.")
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email.value,
        role=user.role.value,
        neighborhood=user.neighborhood,
    )
