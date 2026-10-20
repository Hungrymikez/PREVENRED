"""
Schemas Pydantic: el contrato JSON de la API (lo que entra y sale por HTTP).
Validan forma y tipos; las reglas de negocio las valida el dominio.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from prevenred.identity.domain.mfa import LOGIN_PURPOSE

#: Orden de privilegio de los roles auto-registrables (de menor a mayor). Solo los
#: tres que acepta el formulario público; el dominio tiene el orden completo en
#: `prevenred.identity.domain.role.PRIVILEGE_ORDER`.
ROLE_PREFERENCE = ("CIUDADANO", "VOLUNTARIO", "TECNICO")


class RegisterRequest(BaseModel):
    """Cuerpo de POST /auth/register."""
    full_name: str = Field(min_length=3, max_length=150)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    # Lista: la persona puede registrarse a la vez como Técnico y Voluntario.
    # Al menos un rol (criterio de aceptación de CU-01).
    roles: list[Literal["CIUDADANO", "TECNICO", "VOLUNTARIO"]] = Field(min_length=1, max_length=3)
    neighborhood: str = Field(min_length=1, max_length=100)
    privacy_notice_version: str = Field(default="v1", max_length=20)
    accepted_terms: bool

    @property
    def role(self) -> str:
        """Rol efectivo que mostrará la API (el de mayor privilegio de `roles`).

        La API envía la lista completa al dominio; esta propiedad solo sirve para
        logs o pantallas que necesiten un único rol.
        """
        return max(self.roles, key=lambda code: ROLE_PREFERENCE.index(code))


class UserResponse(BaseModel):
    """Datos públicos de una cuenta (sin contraseña)."""
    id: str
    full_name: str
    email: str
    role: str                     # rol efectivo (el de mayor privilegio)
    roles: list[str] = []         # TODOS los roles, de mayor a menor privilegio
    neighborhood: str


class LoginRequest(BaseModel):
    """Cuerpo de POST /auth/login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta del inicio de sesión: token y rol (o el paso que falta).

    Una cuenta administrativa no recibe sesión al poner la contraseña (RN-07). La
    contraseña sola no basta: responde `200` con `mfa_required: true` y un token
    TEMPORAL de `token_type: "challenge"` que solo sirve para validar el código
    (CU-03). `POST /auth/mfa/verify` lo canjea por la sesión real
    (`token_type: "bearer"`); hasta entonces el token no abre ninguna ruta.
    """
    access_token: str | None = None
    token_type: Literal["bearer", "challenge"] | None = None
    role: str
    mfa_required: bool = False


class MfaRequest(BaseModel):
    """Cuerpo de POST /auth/mfa/request: para qué operación se pide el código."""
    # `login` (CU-02 A1) o `admin_users` (CU-08). El dueño de la cuenta sale del
    # token, no del cuerpo: así nadie puede pedir el código de otra persona.
    purpose: str = LOGIN_PURPOSE
    method: Literal["TOTP", "SMS", "EMAIL"] | None = None


class MfaRequestResponse(BaseModel):
    """Código emitido. `code` va aquí porque v1 no tiene canal de envío (doc 07, O-16).

    Cuando exista el canal real (SMS/correo/TOTP), `code` se quita de la respuesta
    y el código se entrega solo por ese canal.
    """
    challenge_id: str
    method: str
    code: str
    expires_at: datetime


class MfaValidateRequest(BaseModel):
    """Cuerpo de POST /auth/mfa/verify: cuál es la operación y el código tecleado."""
    purpose: str = LOGIN_PURPOSE
    # `str` y no un patrón de 6 dígitos: un código mal formado debe contar como
    # intento fallido (CU-03 E1) y no como error de validación que se pueda distinguir.
    code: str


class MfaVerifyResponse(BaseModel):
    """Verificación satisfecha, en lo que se guarda en el desafío (`mfa_challenges`).

    HOY NO SE USA en `POST /auth/mfa/verify`: ese endpoint responde `TokenResponse`
    para que el cliente reciba ahí el JWT que abre la sesión (CU-03 paso 3). Se
    conserva para una futura ruta de solo-verificación (p. ej. refrescar la
    autorización de `admin_users` sin volver a iniciar sesión).
    """
    user_id: str
    purpose: str
    verified_at: datetime


class CreateAdminAccountRequest(BaseModel):
    """Cuerpo de POST /auth/users (CU-08 A1): cuenta de Inspector o de Administrador.

    La contraseña NO se pide: la genera el sistema y se muestra UNA sola vez.
    """
    full_name: str = Field(min_length=3, max_length=150)
    email: str = Field(max_length=254)
    role: Literal["INSPECTOR", "ADMINISTRADOR"]
    neighborhood: str = Field(min_length=1, max_length=100)
    privacy_notice_version: str = Field(default="v1", max_length=20)


class CreateAdminAccountResponse(BaseModel):
    """La cuenta creada y su contraseña temporal (se cambia en el primer acceso)."""
    user: UserResponse
    temporary_password: str
