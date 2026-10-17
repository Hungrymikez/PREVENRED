"""
Roles de PrevenRed (doc 02/03). El Coordinador se agrupa en Administrador.

Los roles son CÓDIGOS (no ObjectId): así `users.roles` se guarda como texto y
no hay que consultar el catálogo `roles` en cada petición (H-01 del doc 09).

Hay EXACTAMENTE seis roles. Se declaran en un orden fijo porque `roles.md`
conserva el orden de inserción del catálogo y el mínimo privilegio (RN-07)
depende de que el orden no cambie sin querer.
"""
from enum import StrEnum


class Role(StrEnum):
    """Rol de una cuenta. Define qué puede hacer el usuario (control de acceso por rol, RF-03)."""
    CIUDADANO = "CIUDADANO"
    TECNICO = "TECNICO"
    VOLUNTARIO = "VOLUNTARIO"
    PROFESIONAL_SALUD = "PROFESIONAL_SALUD"
    INSPECTOR = "INSPECTOR"
    ADMINISTRADOR = "ADMINISTRADOR"

    @property
    def is_self_registrable(self) -> bool:
        """CU-01: solo las cuentas de la comunidad se auto-registran.

        Ciudadano, Técnico y Voluntario eligen su rol en el formulario público.
        El Profesional de la salud lo habilita el Administrador al verificar su
        título (CU-18) e Inspector y Administrador los crea un Administrador
        (CU-08).
        """
        return self in (Role.CIUDADANO, Role.TECNICO, Role.VOLUNTARIO)

    @property
    def is_administrative(self) -> bool:
        """RN-07: las cuentas administrativas exigen MFA (CU-03)."""
        return self is Role.ADMINISTRADOR

    @property
    def can_see_precise_location(self) -> bool:
        """RN-05: solo los roles operativos ven la ubicación precisa de un reporte.

        El ciudadano ve la zona aproximada (barrio/comuna) para respetar la
        minimización de datos; sin esto, cualquier cuenta podría triangular
        la vivienda de un reportante.
        """
        return self is not Role.CIUDADANO


#: Códigos válidos de rol, para validar texto que viene de la base o de un formulario.
ROLE_CODES = tuple(r.value for r in Role)
