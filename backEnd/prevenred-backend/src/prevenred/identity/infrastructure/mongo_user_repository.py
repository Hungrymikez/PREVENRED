"""
Repositorio de usuarios sobre MongoDB: colección `users` (documento 09, §4).

Convenciones (válidas para TODOS los repositorios):
  - En la BD los campos van en camelCase (como el doc 09); en Python, snake_case.
  - Este archivo es el ÚNICO que conoce la forma del documento Mongo.
  - `roles` se guarda como arreglo de códigos de rol (el doc 09 proponía ObjectId; ver
    docs/09_rectificacion_bd_mongodb.md, hallazgo H-01). Se guardan TODOS los roles de la
    cuenta, sin repetir y de MAYOR a menor privilegio: `roles[0]` es el rol efectivo.
"""
from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from prevenred.identity.domain.repositories import UserDirectory
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.shared.domain.errors import ConflictError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.repository import BaseMongoRepository, utc_aware

COLLECTION = "users"
_ACTIVE, _SUSPENDED = "ACTIVE", "SUSPENDED"


def _roles_from_document(d: dict) -> tuple[Role, ...]:
    """Lee `roles` del documento y devuelve TODOS los roles (o `CITIZEN` por defecto).

    Un documento antiguo o corrupto no puede romper el inicio de sesión: si el
    arreglo falta o viene vacío se asume el rol mínimo (una cuenta sin roles no
    tiene sentido en el modelo de negocio).
    """
    codes = d.get("roles") or []
    roles = [Role(code) for code in codes]          # Role(...) valida el código
    return tuple(roles) if roles else (Role.CIUDADANO,)


def _to_entity(d: dict) -> User:
    """Documento Mongo -> entidad de dominio (sin emitir UserRegistered)."""
    consent = d.get("consent") or {}
    security = d.get("security") or {}
    mfa = security.get("mfa") or {}
    return User.rehydrate(
        id=str(d["_id"]),
        full_name=d["name"],
        email=Email(d["email"]),
        password_hash=d.get("passwordHash") or "",
        roles=_roles_from_document(d),       # todos los roles; el efectivo lo calcula User
        neighborhood=(d.get("location") or {}).get("neighborhood", ""),
        privacy_notice_version=consent.get("privacyNoticeVersion", ""),
        terms_accepted_at=utc_aware(consent.get("acceptedAt")) or utc_aware(d["createdAt"]),
        is_active=d["status"] == _ACTIVE,
        failed_login_attempts=security.get("failedLoginAttempts", 0),
        locked_until=utc_aware(security.get("lockedUntil")),
        mfa_enabled=bool(mfa.get("enabled", False)),
        mfa_secret_enc=mfa.get("secretEnc"),
        device_tokens=tuple(t["token"] for t in d.get("deviceTokens") or [] if t.get("token")),
        precise_location_granted=bool(consent.get("preciseLocationGranted", False)),
        created_at=utc_aware(d["createdAt"]),
    )


def _device_tokens(u: User) -> list[dict]:
    """Formato del doc 09 para `deviceTokens` (CU-06)."""
    return [{"token": t, "registeredAt": utcnow()} for t in u.device_tokens]


def _roles_as_codes(u: User) -> list[str]:
    """`roles` tal como se guarda: TODOS los códigos, de mayor a menor privilegio."""
    return [role.value for role in u.roles]


def _mutable_fields(u: User) -> dict:
    """Campos que el dominio puede cambiar (se usan en $set al actualizar)."""
    return {
        "name": u.full_name,
        "roles": _roles_as_codes(u),
        "status": _ACTIVE if u.is_active else _SUSPENDED,
        "location.neighborhood": u.neighborhood,
        "consent.preciseLocationGranted": u.precise_location_granted,
        "security.failedLoginAttempts": u.failed_login_attempts,
        "security.lockedUntil": u.locked_until,
        "security.mfa.enabled": u.mfa_enabled,
        "security.mfa.secretEnc": u.mfa_secret_enc,
        "deviceTokens": _device_tokens(u),
        "updatedAt": utcnow(),
    }


def _to_document(u: User) -> dict:
    """Entidad -> documento completo (solo al crear)."""
    return {
        "_id": ObjectId(u.id),
        "name": u.full_name,
        "email": u.email.value,
        "phone": None,
        "passwordHash": u.password_hash,
        "roles": _roles_as_codes(u),
        "status": _ACTIVE if u.is_active else _SUSPENDED,
        "verified": False,   # la verificación de técnicos es otro caso (CU-18)
        "location": {"neighborhood": u.neighborhood},
        "consent": {
            "privacyNoticeVersion": u.privacy_notice_version,
            "acceptedAt": u.terms_accepted_at,
            "preciseLocationGranted": u.precise_location_granted,
        },
        "security": {
            "failedLoginAttempts": u.failed_login_attempts,
            "lockedUntil": u.locked_until,
            "mfa": {"enabled": u.mfa_enabled, "secretEnc": u.mfa_secret_enc},
        },
        "deviceTokens": _device_tokens(u),
        "createdAt": u.created_at,
        "updatedAt": u.created_at,
    }


class MongoUserRepository(BaseMongoRepository[User], UserDirectory):
    """UserRepository + consultas de CU-08 sobre la colección `users` de MongoDB."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._users = self._col

    # ---- Traducción exigida por BaseMongoRepository ----
    def to_document(self, user: User) -> dict:
        """Entidad -> documento completo."""
        return _to_document(user)

    def to_entity(self, document: dict) -> User:
        """Documento -> entidad (sin emitir eventos)."""
        return _to_entity(document)

    def updates(self, user: User) -> dict:
        """Campos que cambia identity; nunca toca `phone` ni `verified`."""
        return _mutable_fields(user)

    # ---- Consultas propias del contexto ----
    def get_by_email(self, email: Email) -> User | None:
        """Busca por correo ya normalizado (minúsculas)."""
        doc = self._users.find_one({"email": email.value})
        return _to_entity(doc) if doc else None

    def list_by_role(self, role: str, *, limit: int = 100) -> list[User]:
        """Cuentas activas de un rol, de la más antigua a la más nueva."""
        cursor = (
            self._users.find({"roles": role, "status": _ACTIVE})
            .sort("createdAt", 1)
            .limit(limit)
        )
        return [_to_entity(doc) for doc in cursor]

    def count_active_with_role(self, role: str) -> int:
        """Cuántas cuentas ACTIVAS tienen ese rol (CU-08 E1)."""
        return self._users.count_documents({"roles": role, "status": _ACTIVE})

    def add(self, user: User) -> None:
        """Inserta el usuario.

        El índice único de correo evita duplicados aun con peticiones simultáneas;
        aquí solo le damos un mensaje de negocio (E1 de CU-01).
        """
        try:
            self._users.insert_one(_to_document(user))
        except DuplicateKeyError:
            # Carrera: dos registros simultáneos con el mismo correo (índice único).
            raise self.conflict_message() from None

    @staticmethod
    def conflict_message() -> ConflictError:
        """E1 de CU-01: el correo ya está registrado, con la salida de recuperación."""
        return ConflictError("Ese correo ya está registrado. Puedes recuperar tu acceso.")

