"""Roles de PrevenRed (doc 02/03). El Coordinador se agrupa en Administrador."""
from enum import StrEnum


class Role(StrEnum):
    """Rol de una cuenta. Define qué puede hacer el usuario (control de acceso por rol, RF-03)."""
    CIUDADANO = "ciudadano"
    TECNICO_VOLUNTARIO = "tecnico_voluntario"
    INSPECTOR = "inspector"
    ADMINISTRADOR = "administrador"
    PROFESIONAL_SALUD = "profesional_salud"

    @property
    def is_self_registrable(self) -> bool:
        """CU-01: Inspector y Administrador NO se auto-registran;
        los crea un Administrador (CU-08)."""
        return self in (Role.CIUDADANO, Role.TECNICO_VOLUNTARIO)

    @property
    def is_administrative(self) -> bool:
        """RN-07: las cuentas administrativas exigen MFA (CU-03)."""
        return self is Role.ADMINISTRADOR
