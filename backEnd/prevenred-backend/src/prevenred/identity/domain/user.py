"""
Entidad User: aquí viven las REGLAS DE NEGOCIO de una cuenta.
No sabe nada de HTTP ni de bases de datos.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from prevenred.identity.domain.events import UserAccountCreated, UserRegistered
from prevenred.identity.domain.role import Role, highest_privilege_role, normalize_roles
from prevenred.identity.domain.value_objects import Email
from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_text, require_utc

# Parámetros de bloqueo (RNF-14). Valores provisionales hasta definirlos (O-16).
MAX_FAILED_LOGINS = 5
LOCK_DURATION = timedelta(minutes=15)


@dataclass(kw_only=True, eq=False)
class User(Entity):
    """Cuenta de usuario con sus reglas de negocio.

    Un usuario nuevo se crea solo con User.register(...); el repositorio reconstruye
    cuentas existentes con User.rehydrate(...), que NO emite eventos.
    """
    full_name: str
    email: Email
    password_hash: str            # NUNCA la contraseña en claro
    # Una cuenta puede tener VARIOS roles (p. ej. Técnico y Voluntario). Se guardan
    # todos, sin repetir y de mayor a menor privilegio: `roles[0]` es el efectivo.
    # Para leer el rol que manda existe la propiedad `role` (ver abajo).
    roles: tuple[Role, ...]
    neighborhood: str             # barrio/comuna: ubicación aproximada (RN-05 minimización)
    privacy_notice_version: str   # qué versión del aviso aceptó (CU-01 paso 6)
    terms_accepted_at: datetime
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    # CU-03 / RN-07: segundo factor de las cuentas administrativas. El secreto se
    # guarda CIFRADO (`security.mfa.secretEnc`); aquí nunca se maneja en claro.
    mfa_enabled: bool = False
    mfa_secret_enc: str | None = None
    # CU-06: tokens de push del dispositivo (puede haber varios: varios celulares).
    device_tokens: tuple[str, ...] = ()
    # RN-05 / CU-01: consentimiento aparte para compartir la ubicación PRECISA.
    # Sin él, la cuenta solo comparte barrio/comuna.
    precise_location_granted: bool = False
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Deja los roles sin repetir y ordenados por privilegio (la BD siempre así)."""
        self.roles = normalize_roles(self.roles)

    # ---- Rol efectivo ----
    @property
    def role(self) -> Role:
        """Rol de MAYOR PRIVILEGIO de la cuenta (el que decide qué puede hacer).

        Se conserva el nombre `role` en singular a propósito: todo el código que
        autoriza (login, MFA, CU-08, `require_roles`) ya lee `user.role` y sigue
        funcionando sin cambios, aunque la cuenta tenga varios roles guardados.
        Orden: ADMINISTRADOR > INSPECTOR > PROFESIONAL_SALUD > TECNICO >
        VOLUNTARIO > CIUDADANO (ver `PRIVILEGE_ORDER`).
        """
        return highest_privilege_role(self.roles)

    def has_any_role(self, *roles: Role) -> bool:
        """True si la cuenta tiene CUALQUIERA de esos roles (RBAC por lista, RF-03)."""
        return any(role in self.roles for role in roles)

    # ---- Fábrica: la única forma válida de crear un usuario nuevo ----
    @classmethod
    def register(
        cls,
        *,
        full_name: str,
        email: Email,
        password_hash: str,
        roles: "Role | tuple[Role, ...] | list[Role]",
        neighborhood: str,
        privacy_notice_version: str,
        accepted_terms: bool,
    ) -> "User":
        """Crea una cuenta nueva y registra el evento UserRegistered.

        Exige consentimiento (CU-01 A1), roles permitidos y datos básicos.
        `roles` admite uno o varios: la persona puede registrarse a la vez como
        Técnico y Voluntario (CU-01), y se guardan TODOS.
        """
        requested = normalize_roles((roles,) if isinstance(roles, Role) else roles)
        # CU-01 A1: sin aceptar privacidad y términos no se crea la cuenta.
        if not accepted_terms:
            raise ValidationError(
                "Debes aceptar el aviso de privacidad y los términos de uso para crear tu cuenta."
            )
        # CU-01 / RN-07: no hay auto-registro de Inspector ni Administrador.
        forbidden = [r for r in requested if not r.is_self_registrable]
        if forbidden:
            raise ForbiddenError("Ese tipo de cuenta no se puede crear por auto-registro.")
        if len(full_name.strip()) < 3:
            raise ValidationError("Escribe tu nombre completo.")
        if not neighborhood.strip():
            raise ValidationError("Indica tu barrio o comuna.")

        user = cls(
            full_name=full_name.strip(),
            email=email,
            password_hash=password_hash,
            roles=requested,
            neighborhood=neighborhood.strip(),
            privacy_notice_version=privacy_notice_version,
            terms_accepted_at=utcnow(),
        )
        # El evento lleva el rol EFECTIVO (el de mayor privilegio): services crea el
        # perfil según ese rol y no necesita entender cuentas con varios roles.
        user.record_event(UserRegistered(user_id=user.id, role=user.role.value))
        return user

    @classmethod
    def open_administratively(
        cls,
        *,
        full_name: str,
        email: Email,
        password_hash: str,
        roles: "Role | tuple[Role, ...] | list[Role]",
        neighborhood: str,
        privacy_notice_version: str,
        created_by: str,
    ) -> "User":
        """CU-08 A1: crea una cuenta de Inspector/Administrador por encargo de un Administrador.

        Es distinto de `register` en UNA decisión de negocio: quien la crea es el
        Administrador (con su segundo factor verificado, CU-03), no la persona; por
        eso el rol interno sí se admite. Todo lo demás se valida igual y el
        consentimiento se registra a nombre de la entidad en el primer acceso.
        """
        requested = normalize_roles((roles,) if isinstance(roles, Role) else roles)
        if all(role.is_self_registrable for role in requested):
            raise ValidationError(
                "Las cuentas de la comunidad se crean por auto-registro (CU-01)."
            )
        if len(full_name.strip()) < 3:
            raise ValidationError("Escribe el nombre completo de la persona.")
        if not neighborhood.strip():
            raise ValidationError("Indica el barrio o comuna de la cuenta.")

        user = cls(
            full_name=full_name.strip(),
            email=email,
            password_hash=password_hash,
            roles=requested,
            neighborhood=neighborhood.strip(),
            privacy_notice_version=privacy_notice_version,
            terms_accepted_at=utcnow(),
        )
        user.record_event(
            # Evento PROPIO: si se reutilizara `UserRegistered`, `services` crearía
            # un perfil "pendiente de técnico" para un Inspector o un Administrador.
            UserAccountCreated(user_id=user.id, role=user.role.value, created_by=created_by)
        )
        return user

    @classmethod
    def rehydrate(cls, **fields) -> "User":
        """Reconstruye una cuenta YA existente desde la base de datos.

        Es distinto de `register`: no vuelve a exigir el consentimiento ni el rol
        (la cuenta ya existe) y NO emite `UserRegistered` (si no, cada lectura
        "registraría" al usuario y dispararía otra vez CU-17 en services).
        """
        return cls(**fields)

    # ---- Comportamiento de inicio de sesión (CU-02) ----
    def is_locked(self, now: datetime) -> bool:
        """True si la cuenta está bloqueada temporalmente en este momento (CU-02 E2)."""
        return self.locked_until is not None and now < self.locked_until

    def register_failed_login(self, now: datetime) -> None:
        """Suma un fallo y bloquea temporalmente al llegar al máximo (E2)."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= MAX_FAILED_LOGINS:
            self.locked_until = now + LOCK_DURATION
            self.failed_login_attempts = 0

    def register_successful_login(self) -> None:
        """Limpia el contador de fallos y cualquier bloqueo tras un inicio de sesión correcto."""
        self.failed_login_attempts = 0
        self.locked_until = None

    # ---- Segundo factor (CU-03 / RN-07) ----
    def requires_mfa(self) -> bool:
        """True si esta cuenta no puede iniciar sesión sin el segundo factor."""
        return self.role.is_administrative

    def enable_mfa(self, secret_enc: str) -> None:
        """Activa el segundo factor guardando el secreto YA cifrado (RN-07)."""
        require_text(secret_enc, "mfa_secret_enc", max_length=512)
        self.mfa_secret_enc = secret_enc
        self.mfa_enabled = True

    def disable_mfa(self) -> None:
        """Apaga el segundo factor. RN-07 lo PROHÍBE en cuentas administrativas."""
        if self.requires_mfa():
            raise ForbiddenError(
                "Las cuentas administrativas deben mantener la verificación en dos pasos."
            )
        self.mfa_secret_enc = None
        self.mfa_enabled = False

    # ---- Consentimiento de ubicación precisa (RN-05) ----
    def grant_precise_location(self) -> None:
        """La persona autoriza compartir su ubicación precisa (CU-01, RN-05)."""
        self.precise_location_granted = True

    def revoke_precise_location(self) -> None:
        """Retira la autorización: desde ahora solo se comparte barrio/comuna."""
        self.precise_location_granted = False

    def can_share_precise_location(self) -> bool:
        """Solo se comparte la ubicación precisa si la persona lo autorizó."""
        return self.precise_location_granted

    # ---- Tokens de push (CU-06) ----
    def register_device_token(self, token: str) -> None:
        """Asocia un dispositivo para notificaciones push (idempotente)."""
        require_text(token, "device_token", max_length=512)
        if token not in self.device_tokens:
            self.device_tokens = (*self.device_tokens, token)

    def forget_device_token(self, token: str) -> None:
        """Desasocia un dispositivo (p. ej. al cerrar sesión en ese celular)."""
        self.device_tokens = tuple(t for t in self.device_tokens if t != token)

    # ---- Datos personales ----
    def change_name(self, full_name: str) -> None:
        """Cambia el nombre visible, con la misma regla que al registrarse."""
        if len(full_name.strip()) < 3:
            raise ValidationError("Escribe tu nombre completo.")
        self.full_name = full_name.strip()

    def change_password_hash(self, password_hash: str) -> None:
        """Guarda un hash nuevo (CU-02 A2) y desbloquea la cuenta.

        Se desbloquea a propósito: quien restablece el acceso con un enlace válido
        ya demostró ser la dueña o el dueño de la cuenta.
        """
        require_text(password_hash, "password_hash", max_length=512)
        self.password_hash = password_hash
        self.register_successful_login()

    def suspend(self) -> None:
        """Desactiva la cuenta: CU-02 E3 niega el acceso a partir de ese momento."""
        self.is_active = False

    def change_role(self, role: Role) -> None:
        """Cambia el rol de la cuenta (CU-08 paso 6).

        Sustituye el conjunto de roles por el indicado: CU-08 asigna UN rol, así que
        los demás se retiran. El mínimo privilegio (RN-07) se decide en el servidor:
        quién autoriza la operación —CU-03— es la capa de aplicación, y el dominio
        solo impide dejar una cuenta suspendida con un rol nuevo.
        """
        if self.roles == (role,):
            return
        if not self.is_active:
            raise ValidationError("No se puede cambiar el rol de una cuenta suspendida.")
        self.roles = normalize_roles((role,))

    def grant_role(self, role: Role) -> None:
        """Agrega un rol sin quitar los que ya tiene (p. ej. habilita CU-18)."""
        self.roles = normalize_roles((*self.roles, role))

    def revoke_role(self, role: Role) -> None:
        """Retira un rol; la cuenta nunca puede quedarse sin ninguno."""
        remaining = tuple(r for r in self.roles if r is not role)
        if not remaining:
            raise ValidationError("La cuenta debe conservar al menos un rol.")
        self.roles = normalize_roles(remaining)

    def reactivate(self) -> None:
        """Vuelve a habilitar una cuenta suspendida."""
        self.is_active = True

    def record_terms_acceptance(self, privacy_notice_version: str, accepted_at: datetime) -> None:
        """Registra una nueva aceptación del aviso de privacidad (RN-05)."""
        require_text(privacy_notice_version, "privacy_notice_version", max_length=50)
        self.privacy_notice_version = privacy_notice_version
        self.terms_accepted_at = require_utc(accepted_at, "terms_accepted_at")
