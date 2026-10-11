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
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "users"
_ACTIVE, _SUSPENDED = "ACTIVE", "SUSPENDED"


def _to_entity(d: dict) -> User:
    """Documento Mongo -> entidad de dominio."""
    return User(
        id=str(d["_id"]),
        full_name=d["name"],
        email=Email(d["email"]),
        password_hash=d["passwordHash"],
        role=Role(d["roles"][0]),            # el dominio maneja un rol por cuenta
        neighborhood=d["location"]["neighborhood"],
        privacy_notice_version=d["consent"]["privacyNoticeVersion"],
        terms_accepted_at=as_utc(d["consent"]["acceptedAt"]),
        is_active=d["status"] == _ACTIVE,
        failed_login_attempts=d["security"]["failedLoginAttempts"],
        locked_until=as_utc(d["security"]["lockedUntil"]),
        created_at=as_utc(d["createdAt"]),
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
        "verified": False,   # la verificación de técnicos es otro caso (CU-18)
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
        """Devuelve None si el id no tiene formato de ObjectId o no existe."""
        if not ObjectId.is_valid(user_id):
            return None
        doc = self._users.find_one({"_id": ObjectId(user_id)})
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
        self._users.update_one({"_id": ObjectId(user.id)}, {"$set": _mutable_fields(user)})
