"""
Repositorio de usuarios sobre MongoDB: colección `users` (documento 09, §4).

Convenciones (válidas para TODOS los repositorios):
  - En la BD los campos van en camelCase (como el doc 09); en Python, snake_case.
  - Este archivo es el ÚNICO que conoce la forma del documento Mongo.
  - `roles` se guarda como arreglo de códigos de rol (el doc 09 proponía ObjectId; ver
    docs/09_rectificacion_bd_mongodb.md, hallazgo H-01).
"""

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from prevenred.identity.domain.repositories import UserRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.shared.domain.errors import ConflictError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "users"
_ACTIVE, _SUSPENDED = "ACTIVE", "SUSPENDED"


def _parse_role(raw: object) -> Role:
    """Interpreta el rol aceptando strings, listas, mayúsculas, minúsculas y aliases."""
    if isinstance(raw, Role):
        return raw
    if isinstance(raw, list) and raw:
        raw = raw[0]
    if isinstance(raw, str):
        val = raw.strip()
        try:
            return Role(val.lower())
        except ValueError:
            pass
        try:
            return Role[val.upper()]
        except KeyError:
            pass
    return Role.CIUDADANO


def _to_entity(d: dict) -> User:
    """Documento Mongo -> entidad de dominio.

    Tolerante a formatos camelCase (MongoDB diseño doc 09) y snake_case (scripts y pruebas).
    """
    user_id = EntityId(str(d.get("_id") or d.get("id")))
    full_name = d.get("name") or d.get("fullName") or d.get("full_name") or ""

    raw_email = d.get("email") or ""
    email = Email(raw_email) if isinstance(raw_email, str) else raw_email

    password_hash = d.get("passwordHash") or d.get("password_hash") or d.get("password") or ""

    role_candidate = d.get("roles") if d.get("roles") is not None else d.get("role")
    role = _parse_role(role_candidate)

    # Ubicación / barrio
    location = d.get("location") if isinstance(d.get("location"), dict) else {}
    neighborhood = location.get("neighborhood") or d.get("neighborhood") or "Pereira"

    # Consentimiento
    consent = d.get("consent") if isinstance(d.get("consent"), dict) else {}
    privacy_version = (
        consent.get("privacyNoticeVersion")
        or consent.get("privacy_notice_version")
        or d.get("privacyNoticeVersion")
        or d.get("privacy_notice_version")
        or "v1"
    )
    raw_accepted_at = (
        consent.get("acceptedAt")
        or consent.get("accepted_at")
        or d.get("acceptedAt")
        or d.get("accepted_at")
        or d.get("termsAcceptedAt")
        or d.get("terms_accepted_at")
        or d.get("createdAt")
        or d.get("created_at")
        or utcnow()
    )
    terms_accepted_at = as_utc(raw_accepted_at)

    # Estado activo / suspendido
    if "is_active" in d:
        is_active = bool(d["is_active"])
    elif "isActive" in d:
        is_active = bool(d["isActive"])
    elif "status" in d:
        is_active = d["status"] == _ACTIVE
    else:
        is_active = True

    # Seguridad (bloqueo / reintentos)
    security = d.get("security") if isinstance(d.get("security"), dict) else {}
    failed_attempts = (
        security.get("failedLoginAttempts")
        or security.get("failed_login_attempts")
        or d.get("failedLoginAttempts")
        or d.get("failed_login_attempts")
        or 0
    )
    raw_locked_until = (
        security.get("lockedUntil")
        or security.get("locked_until")
        or d.get("lockedUntil")
        or d.get("locked_until")
    )
    locked_until = as_utc(raw_locked_until) if raw_locked_until else None

    # Fecha de creación
    raw_created_at = d.get("createdAt") or d.get("created_at") or utcnow()
    created_at = as_utc(raw_created_at)

    return User(
        id=user_id,
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role=role,
        neighborhood=neighborhood,
        privacy_notice_version=privacy_version,
        terms_accepted_at=terms_accepted_at,
        is_active=is_active,
        failed_login_attempts=int(failed_attempts),
        locked_until=locked_until,
        created_at=created_at,
    )


def _mutable_fields(u: User) -> dict:
    """Campos que el dominio puede cambiar (se usan en $set al actualizar)."""
    return {
        "name": u.full_name,
        "roles": [u.role.value],
        "status": _ACTIVE if u.is_active else _SUSPENDED,
        "location.neighborhood": u.neighborhood,
        "security.failedLoginAttempts": u.failed_login_attempts,
        "security.lockedUntil": u.locked_until,
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
        "roles": [u.role.value],
        "status": _ACTIVE if u.is_active else _SUSPENDED,
        "verified": False,  # la verificación de técnicos es otro caso (CU-18)
        "location": {"neighborhood": u.neighborhood},
        "consent": {
            "privacyNoticeVersion": u.privacy_notice_version,
            "acceptedAt": u.terms_accepted_at,
        },
        "security": {"failedLoginAttempts": 0, "lockedUntil": None},
        "createdAt": u.created_at,
        "updatedAt": u.created_at,
    }


class MongoUserRepository(UserRepository):
    """UserRepository sobre la colección `users` de MongoDB."""

    def __init__(self, db: Database) -> None:
        self._users = db[COLLECTION]

    def get_by_id(self, user_id: str) -> User | None:
        """Devuelve None si no existe o el formato es inválido."""
        if ObjectId.is_valid(user_id):
            doc = self._users.find_one({"_id": ObjectId(user_id)}) or self._users.find_one(
                {"_id": user_id}
            )
        else:
            doc = self._users.find_one({"_id": user_id})
        return _to_entity(doc) if doc else None

    def get_by_email(self, email: Email) -> User | None:
        """Busca por correo ya normalizado (minúsculas)."""
        doc = self._users.find_one({"email": email.value})
        return _to_entity(doc) if doc else None

    def add(self, user: User) -> None:
        """Inserta el usuario.

        El índice único de correo evita duplicados aun con peticiones simultáneas.
        """
        try:
            self._users.insert_one(_to_document(user))
        except DuplicateKeyError:
            # Carrera: dos registros simultáneos con el mismo correo (índice único).
            raise ConflictError(
                "Ese correo ya está registrado. Puedes recuperar tu acceso."
            ) from None

    def update(self, user: User) -> None:
        # $set solo de lo que el dominio controla: no pisa campos de otros contextos
        # (p. ej. `verified` o `phone`, que cambian en otros casos de uso).
        """Actualiza solo los campos que controla el dominio ($set).

        No toca los campos que escriben otros contextos.
        """
        if ObjectId.is_valid(user.id):
            query = {"$or": [{"_id": ObjectId(user.id)}, {"_id": user.id}]}
        else:
            query = {"_id": user.id}
        self._users.update_one(query, {"$set": _mutable_fields(user)})
