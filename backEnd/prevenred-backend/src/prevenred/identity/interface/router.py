"""Rutas HTTP del contexto identity. Solo traducen HTTP <-> casos de uso."""
from fastapi import APIRouter, Depends

from prevenred.identity.application.login_user import LoginCommand, LoginUser
from prevenred.identity.application.manage_users import CreateAccountCommand, ManageUsers
from prevenred.identity.application.ports import TokenPayload, TokenService
from prevenred.identity.application.register_user import RegisterUser, RegisterUserCommand
from prevenred.identity.application.validate_mfa import (
    RequestMfaCode,
    RequestMfaCommand,
    VerifyMfaCode,
    VerifyMfaCommand,
)
from prevenred.identity.domain.repositories import UserRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.value_objects import SecondFactorMethod
from prevenred.identity.interface.dependencies import (
    get_current_token,
    get_login_user,
    get_manage_users,
    get_mfa_token,
    get_register_user,
    get_request_mfa,
    get_token_service,
    get_user_repository,
    get_verify_mfa,
    require_roles,
)
from prevenred.identity.interface.schemas import (
    CreateAdminAccountRequest,
    CreateAdminAccountResponse,
    LoginRequest,
    MfaRequest,
    MfaRequestResponse,
    MfaValidateRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from prevenred.shared.domain.errors import NotFoundError

router = APIRouter(prefix="/api/v1/auth", tags=["Acceso (M01)"])


def _user_response(user) -> UserResponse:  # noqa: ANN001 - entidad `User` del dominio
    """Proyecta la cuenta a su representación pública (nunca la contraseña)."""
    return UserResponse(
        id=user.id, full_name=user.full_name, email=user.email.value,
        role=user.role.value, roles=[r.value for r in user.roles],
        neighborhood=user.neighborhood,
    )


@router.post("/register", response_model=UserResponse, status_code=201, summary="CU-01 Registrarse")
def register(body: RegisterRequest, use_case: RegisterUser = Depends(get_register_user)):
    """CU-01: crea una cuenta y devuelve sus datos públicos (nunca la contraseña)."""
    user = use_case.execute(
        RegisterUserCommand(
            full_name=body.full_name, email=body.email, password=body.password,
            roles=tuple(Role(code) for code in body.roles),
            neighborhood=body.neighborhood,
            privacy_notice_version=body.privacy_notice_version,
            accepted_terms=body.accepted_terms,
        )
    )
    return _user_response(user)


@router.post("/login", response_model=TokenResponse, summary="CU-02 Iniciar sesión")
def login(
    body: LoginRequest,
    use_case: LoginUser = Depends(get_login_user),
    tokens: TokenService = Depends(get_token_service),
):
    """CU-02: valida las credenciales y devuelve el token de sesión.

    Si la cuenta es administrativa (RN-07) NO se emite sesión: responde `200` con
    `mfa_required: true` y un token temporal (`token_type: "challenge"`) que solo
    sirve para validar el código (CU-03). Ese token no abre ninguna ruta protegida:
    el login deja abierto además el desafío del segundo factor.
    """
    result = use_case.execute(LoginCommand(email=body.email, password=body.password))
    if result.mfa_required:
        return TokenResponse(
            access_token=tokens.issue_mfa_challenge(result.user_id, result.roles),
            token_type="challenge",
            role=result.role.value,
            mfa_required=True,
        )
    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        role=result.role.value,
        mfa_required=False,
    )


@router.post(
    "/mfa/request",
    response_model=MfaRequestResponse,
    summary="CU-03 Pedir el código del segundo factor",
)
def request_mfa_code(
    body: MfaRequest,
    token: TokenPayload = Depends(get_mfa_token),
    use_case: RequestMfaCode = Depends(get_request_mfa),
):
    """CU-03 paso 1 / A1: entrega un código nuevo para la operación indicada.

    La cuenta es la DUEÑA DEL TOKEN (nunca otra). Sirve para reenviar el código
    (A1) cuando el anterior venció o no llegó; el desafío ABIERTO se reutiliza
    mientras siga vigente, para no saltarse el bloqueo por intentos (E2).
    """
    view = use_case.execute(
        RequestMfaCommand(
            user_id=token.user_id,
            purpose=body.purpose,
            method=SecondFactorMethod(body.method) if body.method else None,
        )
    )
    return MfaRequestResponse(
        challenge_id=view.challenge_id,
        method=str(view.method),
        code=str(view.code),
        expires_at=view.expires_at,
    )


@router.post(
    "/mfa/verify",
    response_model=TokenResponse,
    summary="CU-03 Validar el código y abrir la sesión",
)
def verify_mfa_code(
    body: MfaValidateRequest,
    token: TokenPayload = Depends(get_mfa_token),
    use_case: VerifyMfaCode = Depends(get_verify_mfa),
    users: UserRepository = Depends(get_user_repository),
    tokens: TokenService = Depends(get_token_service),
):
    """CU-03 paso 3: valida el código y autoriza la operación.

    Con `purpose=login` recibe el token temporal del login administrativo
    (`token_type: "challenge"`) y lo canjea por el token de sesión (`bearer`): es
    el ÚNICO sitio donde una cuenta administrativa obtiene su JWT (RN-07).
    Con otro propósito (p. ej. `admin_users`) recibe la sesión ya abierta y solo
    deja la operación autorizada por unos minutos.
    Un código incorrecto responde `401` y consume un intento; agotados los
    intentos, `429` y la operación queda bloqueada (E2).
    """
    use_case.execute(VerifyMfaCommand(user_id=token.user_id, purpose=body.purpose, code=body.code))
    user = users.get_by_id(token.user_id)
    if user is None:                                # desapareció entre los dos pasos
        raise NotFoundError("La cuenta ya no existe.")
    if token.is_mfa_challenge:                      # solo el login abre sesión
        user.register_successful_login()            # el segundo factor cerró el acceso
        users.update(user)
        return TokenResponse(
            access_token=tokens.issue(user.id, user.roles),
            token_type="bearer",
            role=user.role.value,
            mfa_required=False,
        )
    # Operación crítica: la sesión sigue igual y el desafío queda VERIFICADO.
    return TokenResponse(
        access_token=None,
        token_type=None,
        role=user.role.value,
        mfa_required=False,
    )


@router.post(
    "/users",
    response_model=CreateAdminAccountResponse,
    status_code=201,
    summary="CU-08 Crear cuenta de Inspector o Administrador",
    dependencies=[Depends(require_roles(Role.ADMINISTRADOR))],
)
def create_admin_account(
    body: CreateAdminAccountRequest,
    token: TokenPayload = Depends(get_current_token),
    use_case: ManageUsers = Depends(get_manage_users),
):
    """CU-08 A1: crea la cuenta con credenciales iniciales generadas por el sistema.

    Exige un Administrador (RBAC) Y la verificación en dos pasos de la operación
    `admin_users` vigente (RN-07, comprobada en el dominio): el token prueba quién
    entró; el desafío verificado prueba que pasó el segundo factor.
    """
    managed = use_case.create_account(
        CreateAccountCommand(
            actor_id=token.user_id,
            full_name=body.full_name, email=body.email, role=Role(body.role),
            neighborhood=body.neighborhood,
            privacy_notice_version=body.privacy_notice_version,
        )
    )
    return CreateAdminAccountResponse(
        user=_user_response(managed.user),
        temporary_password=managed.temporary_password,
    )


@router.get("/me", response_model=UserResponse, summary="Usuario de la sesión actual")
def me(
    token: TokenPayload = Depends(get_current_token),
    users: UserRepository = Depends(get_user_repository),
):
    """Devuelve los datos de la cuenta dueña del token."""
    user = users.get_by_id(token.user_id)
    if user is None:
        raise NotFoundError("La cuenta ya no existe.")
    return _user_response(user)

