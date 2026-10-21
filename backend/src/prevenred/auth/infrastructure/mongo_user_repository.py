"""
Repositorio de usuarios sobre MongoDB: colección `users` de PrevenRED2.

Este archivo es el único que conoce la forma del documento. Se ESCRIBE siempre con
la forma de PrevenRED2 (un voluntario queda así: phone, password_hash, roles
['VOLUNTARIO'], status ACTIVO, verified, location Point [lng, lat], perfil_tecnico
null y perfil_voluntario {habilidades, autorizado}).

Se LEE de forma tolerante: también acepta documentos antiguos en camelCase (doc 09)
o snake_case (scripts y pruebas), para no romper datos ya cargados.
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
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "users"
_ACTIVO, _SUSPENDIDO = "ACTIVO", "SUSPENDIDO"
# Valores de estado de documentos antiguos que también significan "activa".
_ACTIVE_STATUSES = {_ACTIVO, "ACTIVE"}

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


def _parse_role(raw: object) -> Role:
    """Interpreta el rol: códigos de PrevenRED2, valores del dominio, listas y aliases."""
    if isinstance(raw, Role):
        return raw
    if isinstance(raw, list) and raw:
        raw = raw[0]
    if isinstance(raw, str):
        val = raw.strip()
        if val in _FROM_DB_ROLE:
            return _FROM_DB_ROLE[val]
        try:
            return Role(val.lower())
        except ValueError:
            pass
        try:
            return Role[val.upper()]
        except KeyError:
            pass
    return Role.CIUDADANO


def _role_code(raw: object) -> str:
    """Código original guardado en Mongo (p. ej. VOLUNTARIO), para no reescribirlo."""
    if isinstance(raw, list) and raw:
        raw = raw[0]
    return raw if isinstance(raw, str) and raw in _FROM_DB_ROLE else ""


def _db_role(u: User) -> str:
    """Conserva VOLUNTARIO o TECNICO si la cuenta ya venía de Mongo."""
    return u.role_code or _TO_DB_ROLE[u.role]


def _coordinates(location: dict) -> tuple[float | None, float | None]:
    coords = location.get("coordinates") if isinstance(location, dict) else None
    if not isinstance(coords, list) or len(coords) != 2:
        return None, None
    return float(coords[0]), float(coords[1])


def _to_entity(d: dict) -> User:
    """Documento Mongo -> entidad de dominio (PrevenRED2, camelCase o snake_case)."""
    user_id = EntityId(str(d.get("_id") or d.get("id")))
    full_name = d.get("name") or d.get("fullName") or d.get("full_name") or ""

    raw_email = d.get("email") or ""
    email = Email(raw_email) if isinstance(raw_email, str) else raw_email

    password_hash = d.get("password_hash") or d.get("passwordHash") or d.get("password") or ""

    raw_role = d.get("roles") if d.get("roles") is not None else d.get("role")
    role = _parse_role(raw_role)

    location = d.get("location") if isinstance(d.get("location"), dict) else {}
    longitude, latitude = _coordinates(location)
    neighborhood = d.get("neighborhood") or location.get("neighborhood") or "Pereira"

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

    if "is_active" in d:
        is_active = bool(d["is_active"])
    elif "isActive" in d:
        is_active = bool(d["isActive"])
    elif "status" in d:
        is_active = d["status"] in _ACTIVE_STATUSES
    else:
        is_active = True

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

    volunteer = d.get("perfil_voluntario") if isinstance(d.get("perfil_voluntario"), dict) else None
    technical = d.get("perfil_tecnico") if isinstance(d.get("perfil_tecnico"), dict) else None

    return User(
        id=user_id,
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role=role,
        neighborhood=neighborhood,
        privacy_notice_version=privacy_version,
        terms_accepted_at=as_utc(raw_accepted_at),
        is_active=is_active,
        failed_login_attempts=int(failed_attempts),
        locked_until=as_utc(raw_locked_until) if raw_locked_until else None,
        created_at=as_utc(d.get("createdAt") or d.get("created_at") or utcnow()),
        phone=d.get("phone") or "",
        latitude=latitude,
        longitude=longitude,
        role_code=_role_code(raw_role),
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
    """Entidad -> documento con la forma de users en PrevenRED2 (solo al crear)."""
    technical, volunteer = _profiles(u)
    document = {
        "_id": ObjectId(u.id),
        "name": u.full_name,
        "email": u.email.value,
        "phone": u.phone or "",
        "password_hash": u.password_hash,
        "roles": [_db_role(u)],
        "status": _ACTIVO if u.is_active else _SUSPENDIDO,
        "verified": False,  # la verificación de técnicos es otro caso (CU-18)
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
        document["location"] = {"type": "Point", "coordinates": [u.longitude, u.latitude]}
    return document


def _id_query(user_id: str) -> dict:
    """Busca por ObjectId y, por compatibilidad, también por el id guardado como texto."""
    if ObjectId.is_valid(user_id):
        return {"$or": [{"_id": ObjectId(user_id)}, {"_id": user_id}]}
    return {"_id": user_id}


class MongoUserRepository(UserRepository):
    """UserRepository sobre la colección `users` de MongoDB."""

    def __init__(self, db: Database) -> None:
        self._users = db[COLLECTION]

    def get_by_id(self, user_id: str) -> User | None:
        """Devuelve None si no existe."""
        doc = self._users.find_one(_id_query(user_id))
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
        """Actualiza solo los campos que controla el dominio ($set).

        No pisa campos que escriben otros contextos (p. ej. `verified` o `phone`).
        """
        self._users.update_one(_id_query(user.id), {"$set": _mutable_fields(user)})
