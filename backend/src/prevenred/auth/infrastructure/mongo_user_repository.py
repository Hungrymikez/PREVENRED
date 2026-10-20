"""
Repositorio de usuarios sobre MongoDB: colección `users` de PrevenRED2.

Este archivo es el único que conoce la forma del documento. Un voluntario
queda así: phone, password_hash, roles ['VOLUNTARIO'], status ACTIVO,
verified, location Point [lng, lat], perfil_tecnico null y perfil_voluntario
{habilidades, autorizado}.
"""
from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from prevenred.auth.domain.repositories import UserRepository
from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.shared.domain.errors import ConflictError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "users"
_ACTIVO, _SUSPENDIDO = "ACTIVO", "SUSPENDIDO"

# Códigos de PrevenRED2. El dominio sigue usando sus propios valores.
_TO_DB_ROLE = {
    Role.CIUDADANO: "CIUDADANO",
    # El auto-registro de técnico/voluntario se guarda como VOLUNTARIO,
    # que es el código que ya usan las cuentas de ese tipo en PrevenRED2.
    Role.TECNICO_VOLUNTARIO: "VOLUNTARIO",
    Role.INSPECTOR: "INSPECTOR",
    Role.ADMINISTRADOR: "ADMINISTRADOR",
    Role.PROFESIONAL_SALUD: "PROFESIONAL_SALUD",
}
_FROM_DB_ROLE = {
    "CIUDADANO": Role.CIUDADANO,
    "TECNICO": Role.TECNICO_VOLUNTARIO,
    "VOLUNTARIO": Role.TECNICO_VOLUNTARIO,
    "INSPECTOR": Role.INSPECTOR,
    "ADMINISTRADOR": Role.ADMINISTRADOR,
    "PROFESIONAL_SALUD": Role.PROFESIONAL_SALUD,
}


def _role_from_db(code: str) -> Role:
    try:
        return _FROM_DB_ROLE[code]
    except KeyError:
        return Role(code.lower())


def _db_role(u: User) -> str:
    """Conserva VOLUNTARIO o TECNICO si la cuenta ya venía de Mongo."""
    return u.role_code or _TO_DB_ROLE[u.role]


def _coordinates(location: dict) -> tuple[float | None, float | None]:
    coords = location.get("coordinates") if isinstance(location, dict) else None
    if not isinstance(coords, list) or len(coords) != 2:
        return None, None
    return float(coords[0]), float(coords[1])


def _to_entity(d: dict) -> User:
    """Documento Mongo de PrevenRED2 -> entidad de dominio."""
    consent = d.get("consent") or {}
    security = d.get("security") or {}
    longitude, latitude = _coordinates(d.get("location") or {})
    volunteer = d.get("perfil_voluntario") if isinstance(d.get("perfil_voluntario"), dict) else None
    technical = d.get("perfil_tecnico") if isinstance(d.get("perfil_tecnico"), dict) else None
    accepted_at = consent.get("acceptedAt") or d.get("createdAt")
    code = d["roles"][0]
    return User(
        id=str(d["_id"]),
        full_name=d["name"],
        email=Email(d["email"]),
        password_hash=d.get("password_hash") or d["passwordHash"],
        role=_role_from_db(code),
        neighborhood=d.get("neighborhood") or "",
        privacy_notice_version=consent.get("privacyNoticeVersion") or "v1",
        terms_accepted_at=as_utc(accepted_at),
        is_active=d.get("status") == _ACTIVO,
        failed_login_attempts=int(security.get("failedLoginAttempts") or 0),
        locked_until=as_utc(security.get("lockedUntil")),
        created_at=as_utc(d["createdAt"]),
        phone=d.get("phone") or "",
        latitude=latitude,
        longitude=longitude,
        role_code=code,
        volunteer_skills=list(volunteer.get("habilidades") or []) if volunteer else [],
        volunteer_authorized=bool(volunteer.get("autorizado")) if volunteer else False,
        has_volunteer_profile=volunteer is not None,
        technical_profile=technical,
    )


def _profiles(u: User) -> tuple[dict | None, dict | None]:
    """perfil_tecnico y perfil_voluntario, null cuando la cuenta no los tiene."""
    if u.role_code and not u.has_volunteer_profile:
        return u.technical_profile, None
    if u.has_volunteer_profile or u.role is Role.TECNICO_VOLUNTARIO:
        return u.technical_profile, {
            "habilidades": list(u.volunteer_skills),
            "autorizado": u.volunteer_authorized,
        }
    return None, None


def _mutable_fields(u: User) -> dict:
    """Campos que el dominio puede cambiar (se usan en $set al actualizar)."""
    return {
        "name": u.full_name,
        "roles": [_db_role(u)],
        "status": _ACTIVO if u.is_active else _SUSPENDIDO,
        "neighborhood": u.neighborhood,
        "security.failedLoginAttempts": u.failed_login_attempts,
        "security.lockedUntil": u.locked_until,
        "updatedAt": utcnow(),
    }


def _to_document(u: User) -> dict:
    """Entidad -> documento con la forma de users en PrevenRED2."""
    technical, volunteer = _profiles(u)
    document = {
        "_id": ObjectId(u.id),
        "name": u.full_name,
        "email": u.email.value,
        "phone": u.phone or "",
        "password_hash": u.password_hash,
        "roles": [_db_role(u)],
        "status": _ACTIVO if u.is_active else _SUSPENDIDO,
        "verified": False,
        "perfil_tecnico": technical,
        "perfil_voluntario": volunteer,
        "neighborhood": u.neighborhood,
        "consent": {
            "privacyNoticeVersion": u.privacy_notice_version,
            "acceptedAt": u.terms_accepted_at,
        },
        "security": {"failedLoginAttempts": 0, "lockedUntil": None},
        "createdAt": u.created_at,
        "updatedAt": u.created_at,
    }
    if u.longitude is not None and u.latitude is not None:
        document["location"] = {
            "type": "Point",
            "coordinates": [u.longitude, u.latitude],
        }
    return document


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
        if not user.role_code:
            user.role_code = _db_role(user)
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
