"""
Schemas Pydantic: el contrato JSON de la API (lo que entra y sale por HTTP).
Validan forma y tipos; las reglas de negocio las valida el dominio.
"""
from typing import Literal

from pydantic import BaseModel, Field

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
    """Respuesta del inicio de sesión: token y rol."""
    access_token: str
    token_type: str = "bearer"
    role: str
