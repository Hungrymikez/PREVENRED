"""
CU-08 · Gestionar usuarios y roles (flujos A y E).

El Administrador decide; este caso de uso comprueba que la acción esté permitida,
la aplica, la audita (CU-05) y avisa al afectado. Las reglas de una cuenta viven
en `User`; aquí se orquesta y se aplican las de la ficha:

  A1  crear cuenta de Inspector o Administrador con credenciales iniciales
  A2  suspender una cuenta: se bloquea el acceso y se revocan sus sesiones
  E1  el cambio dejaría la plataforma sin administradores o elevaría
      privilegios sin autorización => se impide
  E2  la cuenta ya no existe o cambió mientras tanto => se informa y se recarga
  E3  falla la auditoría => el cambio NO se aplica

RN-07: toda operación exige que quien la hace sea Administrador **con segundo
factor verificado** (CU-03). La verificación se comprueba en el dominio: el
desafío de la operación debe estar `VERIFICADO` para el mismo actor.

Las acciones (crear, cambiar rol, suspender, reactivar) se agrupan en un
solo caso de uso con un comando por acción; así el cableado de la interfaz no
repite las mismas dependencias."""
from dataclasses import dataclass

from prevenred.identity.application.ports import PasswordHasher
from prevenred.identity.application.security import temporary_password
from prevenred.identity.domain.mfa import VERIFICATION_TTL
from prevenred.identity.domain.repositories import (
    MfaChallengeRepository,
    RoleAssignmentAudit,
    SessionRevoker,
    UserDirectory,
)
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email, validate_password_strength
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from prevenred.shared.domain.events import utcnow

#: Roles que un Administrador puede crear desde CU-08 (A1: Inspector y Administrador).
CREATABLE_ROLES = (Role.INSPECTOR, Role.ADMINISTRADOR)

#: Operación que protege las acciones de CU-08 con el segundo factor (CU-03).
MFA_PURPOSE = "admin_users"


@dataclass(frozen=True)
class CreateAccountCommand:
    """CU-08 A1: crear la cuenta de un Inspector o de un Administrador."""
    actor_id: str
    full_name: str
    email: str
    role: Role
    neighborhood: str
    privacy_notice_version: str = "v1"


@dataclass(frozen=True)
class ChangeRoleCommand:
    """CU-08 paso 2/4: asignar o cambiar el rol de una cuenta existente."""
    actor_id: str
    user_id: str
    role: Role
    # E2: rol que el administrador vio en pantalla. Si otro ya lo cambió, se
    # informa y se recarga en vez de pisar el cambio ajeno.
    current_role: Role | None = None


@dataclass(frozen=True)
class ChangeStatusCommand:
    """CU-08 paso 2/4: suspender (A2) o reactivar una cuenta."""
    actor_id: str
    user_id: str


@dataclass(frozen=True)
class ManagedAccount:
    """Resultado: la cuenta afectada y, solo al crearla, la contraseña temporal."""
    user: User
    temporary_password: str | None = None


class ManageUsers:
    """Caso de uso CU-08: crear cuentas administrativas, asignar roles y suspender."""

    def __init__(
        self,
        users: UserDirectory,
        challenges: MfaChallengeRepository,
        hasher: PasswordHasher,
        sessions: SessionRevoker,
        audit: RoleAssignmentAudit,
        events: EventBus,
    ) -> None:
        """`UserDirectory` ya cumple `UserRepository` + `LastAdminGuard` (E1)."""
        self._users, self._challenges, self._hasher = users, challenges, hasher
        self._sessions, self._audit_log, self._events = sessions, audit, events

    # ---- Reglas compartidas ----
    def _require_mfa_verified_actor(self, actor_id: str) -> User:
        """RN-07 + CU-03: solo un Administrador con el segundo factor verificado.

        Se exige el desafío VERIFICADO de la operación `admin_users` para el mismo
        actor: el token prueba *quién* entró, el desafío prueba que esa misma
        persona pasó el segundo factor y que la autorización sigue vigente.
        """
        actor = self._users.get_by_id(actor_id)
        if actor is None or not actor.is_active or not actor.role.is_administrative:
            raise ForbiddenError("No tienes permiso para administrar usuarios.")

        challenge = self._challenges.get_latest_verified(
            actor.id, MFA_PURPOSE, since=utcnow() - VERIFICATION_TTL
        )
        if challenge is None or challenge.purpose != MFA_PURPOSE:
            raise ForbiddenError(
                "Las operaciones de administración exigen la verificación en dos pasos."
            )
        challenge.require_satisfied()
        return actor

    def _publish(self, entity: User) -> None:
        """Publica los eventos del cambio (solo después de guardarlo)."""
        for event in entity.pull_events():
            self._events.publish(event)

    def _record_audit(
        self, *, actor_id: str, action: str, target_id: str, details: dict
    ) -> None:
        """CU-05 (E3): sin auditoría registrada el cambio no se aplica.

        Se audita ANTES de escribir el cambio. Si `record` falla, la excepción
        sube y el cambio no se guarda; así nunca queda un cambio sin rastro.
        """
        self._audit_log.record(
            actor_id=actor_id, action=action, target_id=target_id, details=details
        )

    # ---- A1: crear una cuenta administrativa ----
    def create_account(self, cmd: CreateAccountCommand) -> ManagedAccount:
        """Crea la cuenta con una contraseña temporal (se cambia al primer acceso).

        El Administrador NO elige la contraseña: la genera el sistema y la muestra
        una sola vez, para que no quede una contraseña compartida circulando.
        """
        self._require_mfa_verified_actor(cmd.actor_id)
        if cmd.role not in CREATABLE_ROLES:
            raise ForbiddenError(
                "Desde aquí solo se crean cuentas de Inspector o de Administrador."
            )
        email = Email(cmd.email)
        if self._users.get_by_email(email) is not None:      # E1 de CU-01
            raise ConflictError("Ese correo ya está registrado. Puedes recuperar tu acceso.")

        password = temporary_password()
        validate_password_strength(password)
        user = User.open_administratively(     # A1: cuenta creada por el Administrador
            full_name=cmd.full_name,
            email=email,
            password_hash=self._hasher.hash(password),
            roles=(cmd.role,),
            neighborhood=cmd.neighborhood,
            privacy_notice_version=cmd.privacy_notice_version,
            created_by=cmd.actor_id,
        )
        self._users.add(user)
        self._publish(user)
        return ManagedAccount(user=user, temporary_password=password)

    # ---- paso 2/6: asignar o cambiar el rol ----
    def change_role(self, cmd: ChangeRoleCommand) -> ManagedAccount:
        """Cambia el rol de una cuenta (incluye ascender a Administrador).

        E1: ascender a Administrador es elevar privilegios y exige la verificación
        reforzada del actor, que ya se comprobó; además, quien se quita a sí mismo
        el rol de Administrador no puede dejar la plataforma sin administradores.
        """
        self._require_mfa_verified_actor(cmd.actor_id)
        user = self._users.get_by_id(cmd.user_id)
        if user is None:                                     # E2
            raise NotFoundError("El usuario ya no existe. Recarga la lista.")
        if cmd.current_role is not None and user.role is not cmd.current_role:  # E2
            raise ConflictError(
                "El rol de la cuenta cambió mientras tanto. Recarga los datos."
            )
        previous = user.role
        if previous is cmd.role:
            return ManagedAccount(user=user)                 # nada que cambiar

        self_admin = previous.is_administrative
        leaves_admin = not cmd.role.is_administrative
        if user.id == cmd.actor_id and self_admin and leaves_admin:
            raise ForbiddenError(
                "Un Administrador no puede quitarse a sí mismo el rol de Administrador."
            )
        if self_admin and self._users.would_leave_platform_without_admins(user.id):
            raise ConflictError(                             # E1
                "No puedes quitarle el rol al último Administrador de la plataforma."
            )

        self._record_audit(
            actor_id=cmd.actor_id, action="USER_ROLE_CHANGED", target_id=user.id,
            details={"previousRole": previous.value, "newRole": cmd.role.value},
        )
        user.change_role(cmd.role)
        self._users.update(user)
        self._publish(user)                                  # UserRoleChanged (notifica)
        return ManagedAccount(user=user)


    # ---- A2: suspender una cuenta ----
    def suspend(self, cmd: ChangeStatusCommand) -> ManagedAccount:
        """Suspende la cuenta y revoca TODAS sus sesiones abiertas (A2).

        E1: el último Administrador activo no se puede suspender: dejaría la
        plataforma sin nadie que pueda administrarla.
        """
        self._require_mfa_verified_actor(cmd.actor_id)
        user = self._users.get_by_id(cmd.user_id)
        if user is None:                                     # E2
            raise NotFoundError("El usuario ya no existe. Recarga la lista.")
        if not user.is_active:
            return ManagedAccount(user=user)                 # ya estaba suspendida

        if user.role.is_administrative and self._users.would_leave_platform_without_admins(
            user.id
        ):
            raise ConflictError(                             # E1
                "No puedes suspender al último Administrador de la plataforma."
            )

        self._record_audit(
            actor_id=cmd.actor_id, action="USER_SUSPENDED", target_id=user.id,
            details={"role": user.role.value},
        )
        user.suspend()
        self._users.update(user)
        # A2: se bloquea el acceso y se cierran las sesiones que ya estaban abiertas;
        # sin esto, un token vigente seguiría sirviendo hasta que venciera.
        self._sessions.revoke_all(user.id)
        self._publish(user)                                  # UserSuspended (notifica)
        return ManagedAccount(user=user)

    # ---- paso 2: reactivar una cuenta ----
    def reactivate(self, cmd: ChangeStatusCommand) -> ManagedAccount:
        """Vuelve a habilitar una cuenta suspendida."""
        self._require_mfa_verified_actor(cmd.actor_id)
        user = self._users.get_by_id(cmd.user_id)
        if user is None:                                     # E2
            raise NotFoundError("El usuario ya no existe. Recarga la lista.")
        if user.is_active:
            return ManagedAccount(user=user)                 # ya estaba activa

        self._record_audit(
            actor_id=cmd.actor_id, action="USER_REACTIVATED", target_id=user.id,
            details={"role": user.role.value},
        )
        user.reactivate()
        self._users.update(user)
        self._publish(user)
        return ManagedAccount(user=user)
