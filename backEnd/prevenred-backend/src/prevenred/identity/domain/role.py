"""
Roles de PrevenRed (doc 02/03). El Coordinador se agrupa en Administrador.

Los roles son CÓDIGOS (no ObjectId): así `users.roles` se guarda como texto y
no hay que consultar el catálogo `roles` en cada petición (H-01 del doc 09).

Hay EXACTAMENTE seis roles. Se declaran en el orden del catálogo `roles`.
El MÍNIMO PRIVILEGIO (RN-07) NO se deduce de ese orden: una cuenta puede tener
varios roles (Técnico y Voluntario a la vez) y, para autorizar, manda el de
mayor privilegio. Ese orden vive aparte, en `PRIVILEGE_ORDER`.
"""
from collections.abc import Iterable
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

#: Orden de PRIVILEGIO, de menor a mayor (RN-07 / mínimo privilegio).
#:
#: No coincide con el orden de declaración del enum (que sigue el catálogo `roles`):
#: el Voluntario está declarado antes que el Profesional de la salud, pero tiene
#: menos privilegio. Este es el único orden que decide autorizaciones.
PRIVILEGE_ORDER: tuple[Role, ...] = (
    Role.CIUDADANO,
    Role.VOLUNTARIO,
    Role.TECNICO,
    Role.PROFESIONAL_SALUD,
    Role.INSPECTOR,
    Role.ADMINISTRADOR,
)

#: Posición de cada rol: cuanto más alto, más privilegio.
_PRIVILEGE_RANK = {role: rank for rank, role in enumerate(PRIVILEGE_ORDER)}


def privilege_of(role: Role) -> int:
    """Posición del rol en el orden de privilegio (más alto = más privilegio)."""
    return _PRIVILEGE_RANK[role]


def highest_privilege_role(roles: Iterable[Role]) -> Role:
    """Devuelve el rol de mayor privilegio de la cuenta.

    Es la regla que permite tener varios roles sin cambiar nada del resto del
    código: quien es Técnico y Voluntario actúa como Técnico; quien además es
    Administrador, actúa como Administrador (y por eso exige MFA, RN-07).
    """
    candidates = tuple(roles)
    if not candidates:
        raise ValueError("Una cuenta debe tener al menos un rol.")
    return max(candidates, key=privilege_of)


def normalize_roles(roles: Iterable[Role]) -> tuple[Role, ...]:
    """Quita repetidos y ordena de MAYOR a menor privilegio (lo que se guarda en la BD).

    El primer elemento es, por lo tanto, el rol efectivo: así una lectura que solo
    mire `roles[0]` (o una consulta hecha a mano en `mongosh`) ve el rol que manda.
    """
    if any(not isinstance(role, Role) for role in roles):
        raise TypeError("Los roles deben ser valores de Role.")
    unique = dict.fromkeys(roles)          # conserva el orden y quita repetidos
    return tuple(sorted(unique, key=privilege_of, reverse=True))

