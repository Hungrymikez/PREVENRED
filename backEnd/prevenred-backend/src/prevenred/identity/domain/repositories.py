"""
Puerto (interfaz) del repositorio. El dominio dice QUÉ necesita guardar/leer;
la capa infrastructure decide CÓMO (PyMongo, memoria para tests, etc.).
"""
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime

from prevenred.identity.domain.auth import PasswordReset, Session
from prevenred.identity.domain.mfa import MfaChallenge
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email, OneTimeCode, SecondFactorMethod


class UserRepository(ABC):
    """Puerto de persistencia de usuarios (lo implementa la capa infrastructure)."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        """Busca un usuario por su id; devuelve None si no existe."""

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        """Busca un usuario por su correo ya normalizado; devuelve None si no existe."""

    @abstractmethod
    def add(self, user: User) -> None:
        """Guarda un usuario nuevo. Lanza ConflictError si el correo ya existe."""

    @abstractmethod
    def update(self, user: User) -> None:
        """Guarda los cambios de un usuario existente."""

    @abstractmethod
    def list_by_role(self, role: str, *, limit: int = 100) -> list[User]:
        """Lista las cuentas de un rol (p. ej. técnicos para una asignación, CU-38)."""


class SessionRepository(ABC):
    """Puerto de las sesiones revocables (CU-02 A4)."""

    @abstractmethod
    def add(self, session: Session) -> None:
        """Registra una sesión emitida; el índice único de `jti` evita duplicados."""

    @abstractmethod
    def get_by_jti(self, jti: str) -> Session | None:
        """Busca la sesión por el id único del token."""

    @abstractmethod
    def update(self, session: Session) -> None:
        """Guarda la revocación de la sesión."""

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """True si el token fue revocado o no está registrado (falla cerrado)."""


class PasswordResetRepository(ABC):
    """Puerto de los enlaces de recuperación de acceso (CU-02 A2)."""

    @abstractmethod
    def add(self, reset: PasswordReset) -> None:
        """Registra un enlace nuevo."""

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> PasswordReset | None:
        """Busca el enlace por el HASH del token (nunca se busca por el token en claro)."""

    @abstractmethod
    def update(self, reset: PasswordReset) -> None:
        """Guarda el consumo del enlace (`usedAt`)."""

    @abstractmethod
    def invalidate_previous(self, user_id: str) -> None:
        """Anula los enlaces anteriores del usuario: solo el último sirve."""


class MfaChallengeRepository(ABC):
    """Puerto de los desafíos del segundo factor (CU-03).

    El desafío es de la operación en curso, así que se guarda aparte de la cuenta:
    lo lee la capa de aplicación al recibir el código que teclea el administrador.
    """

    @abstractmethod
    def add(self, challenge: MfaChallenge) -> None:
        """Registra un desafío recién abierto (paso 1)."""

    @abstractmethod
    def get_by_id(self, challenge_id: str) -> MfaChallenge | None:
        """Busca el desafío por su id; devuelve None si no existe."""

    @abstractmethod
    def get_pending_by_user(self, user_id: str, purpose: str) -> MfaChallenge | None:
        """Devuelve el desafío ABIERTO (PENDIENTE) de esa operación, si lo hay.

        Se consulta por `(userId, purpose)` y no por el id del desafío para que el
        cliente no pueda "elegir" un desafío antiguo al entregar el código.
        """

    @abstractmethod
    def get_latest_verified(
        self, user_id: str, purpose: str, *, since: datetime
    ) -> MfaChallenge | None:
        """Devuelve la verificación SATISFECHA más reciente de esa operación, si sigue vigente.

        La necesitan las operaciones críticas (CU-08): comprueban que el actor pasó
        el segundo factor hace poco para esta operación concreta. `since` es el
        instante a partir del cual una verificación ya no cuenta.
        """

    @abstractmethod
    def get_blocked_by_user(
        self, user_id: str, purpose: str, *, since: datetime
    ) -> MfaChallenge | None:
        """Devuelve el desafío BLOQUEADO más reciente de esa operación, si es de ahora.

        E2: agotar los intentos no debe confundirse con "no pediste código". Sin
        esto, tras tres fallos el usuario recibiría "pide un código" y podría
        abrir un desafío nuevo, saltándose el bloqueo. `since` acota la consulta a
        los bloqueos recientes (CODE_TTL).
        """

    @abstractmethod
    def update(self, challenge: MfaChallenge) -> None:
        """Guarda el avance del desafío: reintentos, verificación, bloqueo o código nuevo."""

    @abstractmethod
    def expire_stale(self, user_id: str) -> None:
        """Cierra en bloque los desafíos vencidos del usuario (A1 abre uno nuevo)."""


class SecondFactorGateway(ABC):
    """Puerto técnico del segundo factor (CÓMO se emite y se valida el código).

    El dominio decide QUÉ es válido (vigencia, intentos, uso único); esta interfaz
    solo traduce a la tecnología concreta —TOTP de una app autenticadora o un
    código de un solo uso enviado por correo/SMS— y elige el método si se pide `AUTO`.
    """

    @abstractmethod
    def default_method(self) -> SecondFactorMethod:
        """Método que se ofrece cuando la operación no impone uno."""

    @abstractmethod
    def issue_code(
        self, *, secret_enc: str, code_hash: Callable[[str], str]
    ) -> tuple[str, str]:
        """Entrega un código para mostrar o enviar.

        Devuelve `(codigo, secret_enc)`: si la cuenta aún no tiene secreto, se crea
        uno nuevo y se entrega YA cifrado para guardarlo en la cuenta; el secreto
        NUNCA sale en claro de esta capa. `code_hash` es la función con la que la
        aplicación guarda el código (misma que usa `matches`): la implementación la
        invoca para recordar el código vigente sin conocer el algoritmo.
        """

    @abstractmethod
    def matches(self, *, code: OneTimeCode, code_hash: str) -> bool:
        """True si el código corresponde a `code_hash`, con comparación en tiempo constante.

        Se compara contra el HASH guardado en el desafío (no contra el secreto): el
        secreto nunca sale de su forma cifrada y el hash no permite reconstruir el
        código. Con TOTP real, esta operación es la que valida la ventana de tiempo.
        """


class SessionRevoker(ABC):
    """Puerto mínimo de sesiones que necesita CU-08 A2 al suspender una cuenta."""

    @abstractmethod
    def revoke_all(self, user_id: str) -> int:
        """Cierra todas las sesiones abiertas del usuario y devuelve cuántas cerró."""


class RoleAssignmentAudit(ABC):
    """Puerto de auditoría de los cambios de rol y estado (CU-05, incluido en CU-08).

    E3: si la auditoría no se puede registrar, el cambio NO se aplica. La capa de
    aplicación llama a `record` ANTES de confirmar el cambio y, si falla, lanza.
    """

    @abstractmethod
    def record(self, *, actor_id: str, action: str, target_id: str, details: dict) -> None:
        """Registra quién hizo qué sobre qué cuenta. Lanza si no puede registrarlo."""


class LastAdminGuard(ABC):
    """Puerto que responde si una operación dejaría la plataforma sin administradores.

    CU-08 E1: nunca puede quedar la plataforma sin un Administrador activo con
    acceso. La cuenta de la consulta es la que se va a modificar.
    """

    @abstractmethod
    def would_leave_platform_without_admins(self, user_id: str) -> bool:
        """True si, tras suspender o quitarle el rol, no quedaría ningún Administrador."""


class UserDirectory(UserRepository, LastAdminGuard):
    """Consultas de administración sobre las cuentas (CU-08).

    Va aparte de `UserRepository` por responsabilidad: registro e inicio de
    sesión no necesitan contar administradores, y así el puerto básico sigue
    siendo pequeño para las implementaciones de prueba.
    """

    @abstractmethod
    def count_active_with_role(self, role: str) -> int:
        """Cuántas cuentas ACTIVAS tienen ese rol (E1: nunca cero administradores)."""

    def would_leave_platform_without_admins(self, user_id: str) -> bool:
        """Implementación por defecto de `LastAdminGuard` (E1).

        Se calcula sobre `count_active_with_role` para que cualquier implementación
        del directorio herede la regla, en vez de repetirla.
        """
        user = self.get_by_id(user_id)
        if user is None or not user.is_active or not user.role.is_administrative:
            return False        # modificarla no reduce el número de administradores
        return self.count_active_with_role(Role.ADMINISTRADOR.value) <= 1

