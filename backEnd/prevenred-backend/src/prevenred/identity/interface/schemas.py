"""
Schemas Pydantic: el contrato JSON de la API (lo que entra y sale por HTTP).
Validan forma y tipos; las reglas de negocio las valida el dominio.
"""
from typing import Literal

from pydantic import BaseModel, Field


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
        """Rol principal para el dominio (que maneja un rol por cuenta).

        Manda el orden del formulario (Ciudadano, Técnico, Voluntario): quien se
        registra como Técnico y Voluntario actúa como Técnico.
        """
        for role in ("CIUDADANO", "TECNICO", "VOLUNTARIO"):
            if role in self.roles:
                return role
        return self.roles[0]


class UserResponse(BaseModel):
    """Datos públicos de una cuenta (sin contraseña)."""
    id: str
    full_name: str
    email: str
    role: str
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
