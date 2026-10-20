"""
Repositorios de sesiones y enlaces de recuperación (CU-02 A2/A4).

- `sessions`: una fila por token emitido. Se revoca marcando `revokedAt`
  (no se borra) para poder auditar cierres de sesión.
- `password_resets`: se guarda el HASH del token; el enlace vence solo.

Ambas colecciones tienen índice TTL sobre `expiresAt` (ver indexes.py): Mongo borra
los documentos vencidos sin que la aplicación tenga que hacerlo.
"""
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from prevenred.identity.domain.auth import PasswordReset, Session
from prevenred.identity.domain.repositories import PasswordResetRepository, SessionRepository
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

SESSIONS = "sessions"
PASSWORD_RESETS = "password_resets"   # antes `passwordResets` (EQUIVALENCIAS_BD, fila 5)


# ---------------------------------------------------------------- sesiones
def _session_to_entity(d: dict) -> Session:
    """Documento -> Session."""
    return Session(
        id=str(d["_id"]),
        user_id=str(d["userId"]),
        jti=d["jti"],
        expires_at=utc_aware(d["expiresAt"]),
        revoked_at=utc_aware(d.get("revokedAt")),
        created_at=utc_aware(d["createdAt"]),
    )


class MongoSessionRepository(BaseMongoRepository[Session], SessionRepository):
    """SessionRepository sobre la colección `sessions`."""
    collection = SESSIONS

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._sessions = self._col

    def to_document(self, s: Session) -> dict:
        """Sesión -> documento."""
        return {
            "_id": ObjectId(s.id),
            "userId": to_reference(s.user_id),
            "jti": s.jti,
            "expiresAt": s.expires_at,
            "revokedAt": s.revoked_at,
            "createdAt": s.created_at,
        }

    def to_entity(self, document: dict) -> Session:
        """Documento -> sesión."""
        return _session_to_entity(document)

    def updates(self, s: Session) -> dict:
        """Lo único que cambia de una sesión es su revocación."""
        return {"revokedAt": s.revoked_at}

    def get_by_jti(self, jti: str) -> Session | None:
        """Busca la sesión por el id único del token."""
        doc = self._sessions.find_one({"jti": jti})
        return _session_to_entity(doc) if doc else None

    def is_revoked(self, jti: str) -> bool:
        """True si el token no está registrado o ya se revocó.

        Falla cerrado: si la consulta no encuentra la sesión, el token NO se acepta.
        """
        doc = self._sessions.find_one({"jti": jti}, {"revokedAt": 1})
        return doc is None or doc.get("revokedAt") is not None

    def revoke_all(self, user_id: str) -> int:
        """Cierra todas las sesiones abiertas del usuario (p. ej. al suspender la cuenta)."""
        oid = to_object_id(user_id)
        if oid is None:
            return 0
        result = self._sessions.update_many(
            {"userId": oid, "revokedAt": None},
            {"$set": {"revokedAt": utcnow()}},
        )
        return result.modified_count


# ------------------------------------------- enlaces de recuperación de acceso
class MongoPasswordResetRepository(BaseMongoRepository[PasswordReset], PasswordResetRepository):
    """PasswordResetRepository sobre la colección `password_resets`."""
    collection = PASSWORD_RESETS

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._resets = self._col

    @staticmethod
    def _to_document(r: PasswordReset) -> dict:
        """Enlace -> documento. Se guarda el hash, nunca el token."""
        return {
            "_id": ObjectId(r.id),
            "userId": to_reference(r.user_id),
            "tokenHash": r.token_hash,
            "expiresAt": r.expires_at,
            "usedAt": r.used_at,
            "createdAt": r.created_at,
        }

    @staticmethod
    def _to_entity(d: dict) -> PasswordReset:
        """Documento -> enlace."""
        return PasswordReset(
            id=str(d["_id"]),
            user_id=str(d["userId"]),
            token_hash=d["tokenHash"],
            expires_at=utc_aware(d["expiresAt"]),
            used_at=utc_aware(d.get("usedAt")),
            created_at=utc_aware(d["createdAt"]),
        )

    def to_document(self, reset: PasswordReset) -> dict:
        """Enlace -> documento completo."""
        return self._to_document(reset)

    def to_entity(self, document: dict) -> PasswordReset:
        """Documento -> enlace."""
        return self._to_entity(document)

    def updates(self, reset: PasswordReset) -> dict:
        """Solo cambia `usedAt`."""
        return {"usedAt": reset.used_at}

    def get_by_token_hash(self, token_hash: str) -> PasswordReset | None:
        """Busca por el hash del token (el único que conocemos)."""
        doc = self._resets.find_one({"tokenHash": token_hash})
        return self._to_entity(doc) if doc else None

    def invalidate_previous(self, user_id: str) -> None:
        """Vence los enlaces anteriores del usuario: solo el último sirve."""
        oid = to_object_id(user_id)
        if oid is None:
            return
        now: datetime = utcnow()
        self._resets.update_many(
            {"userId": oid, "usedAt": None, "expiresAt": {"$gt": now}},
            {"$set": {"expiresAt": now}},
        )
