"""
Desafíos del segundo factor sobre MongoDB (CU-03).

Colección `mfa_challenges`. Cada documento es UNA verificación en curso de UNA
operación; se guarda aparte de la cuenta a propósito (dos pestañas no comparten
intentos ni se pisan el código).

El código se guarda como HASH (`codeHash`), nunca en claro, igual que el token de
`password_resets`: quien lea la base no puede usarlo. El índice TTL de `expiresAt`
borra los desafíos vencidos sin código extra (ver indexes.py).
"""
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from prevenred.identity.domain.mfa import MfaChallenge
from prevenred.identity.domain.repositories import MfaChallengeRepository
from prevenred.identity.domain.value_objects import SecondFactorMethod
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "mfa_challenges"
_PENDING = "PENDIENTE"


def _to_entity(d: dict) -> MfaChallenge:
    """Documento -> desafío."""
    return MfaChallenge(
        id=str(d["_id"]),
        user_id=str(d["userId"]),
        purpose=d["purpose"],
        method=SecondFactorMethod(d["method"]),
        code_hash=d["codeHash"],
        secret_enc=d.get("secretEnc"),
        expires_at=utc_aware(d["expiresAt"]),
        attempts=d.get("attempts", 0),
        status=d.get("status", _PENDING),
        verified_at=utc_aware(d.get("verifiedAt")),
        last_sent_at=utc_aware(d.get("lastSentAt")) or utc_aware(d["createdAt"]),
        created_at=utc_aware(d["createdAt"]),
    )


def _to_document(c: MfaChallenge) -> dict:
    """Desafío -> documento completo (solo al crear)."""
    return {
        "_id": ObjectId(c.id),
        "userId": to_reference(c.user_id),
        "purpose": c.purpose,
        "method": c.method.value,
        "codeHash": c.code_hash,
        "secretEnc": c.secret_enc,
        "attempts": c.attempts,
        "status": c.status,
        "verifiedAt": c.verified_at,
        "expiresAt": c.expires_at,
        "lastSentAt": c.last_sent_at,
        "createdAt": c.created_at,
    }


class MongoMfaChallengeRepository(
    BaseMongoRepository[MfaChallenge], MfaChallengeRepository
):
    """MfaChallengeRepository sobre la colección `mfa_challenges`."""

    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._challenges = self._col

    # ---- Traducción exigida por BaseMongoRepository ----
    def to_document(self, challenge: MfaChallenge) -> dict:
        """Desafío -> documento completo."""
        return _to_document(challenge)

    def to_entity(self, document: dict) -> MfaChallenge:
        """Documento -> desafío (sin emitir eventos)."""
        return _to_entity(document)

    def updates(self, challenge: MfaChallenge) -> dict:
        """Lo que cambia de un desafío: intentos, estado, código y verificación."""
        return {
            "attempts": challenge.attempts,
            "status": challenge.status,
            "codeHash": challenge.code_hash,
            "expiresAt": challenge.expires_at,
            "lastSentAt": challenge.last_sent_at,
            "verifiedAt": challenge.verified_at,
        }

    # ---- Consultas propias de CU-03 ----
    def get_pending_by_user(self, user_id: str, purpose: str) -> MfaChallenge | None:
        """El desafío abierto de esa operación (el más reciente, si hubiera varios)."""
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = self._challenges.find_one(
            {"userId": oid, "purpose": purpose, "status": _PENDING},
            sort=[("createdAt", -1)],
        )
        return _to_entity(doc) if doc else None

    def get_latest_verified(
        self, user_id: str, purpose: str, *, since: datetime
    ) -> MfaChallenge | None:
        """La verificación satisfecha más reciente de esa operación, si sigue vigente."""
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = self._challenges.find_one(
            {
                "userId": oid,
                "purpose": purpose,
                "status": "VERIFICADO",
                "verifiedAt": {"$gte": since},
            },
            sort=[("verifiedAt", -1)],
        )
        return _to_entity(doc) if doc else None

    def get_blocked_by_user(
        self, user_id: str, purpose: str, *, since: datetime
    ) -> MfaChallenge | None:
        """El bloqueo más reciente de esa operación, si ocurrió hace poco (E2)."""
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = self._challenges.find_one(
            {
                "userId": oid,
                "purpose": purpose,
                "status": "BLOQUEADO",
                "createdAt": {"$gte": since},
            },
            sort=[("createdAt", -1)],
        )
        return _to_entity(doc) if doc else None

    def expire_stale(self, user_id: str) -> None:
        """Cierra en bloque los desafíos vencidos del usuario (A1 abre uno nuevo)."""
        oid = to_object_id(user_id)
        if oid is None:
            return
        self._challenges.update_many(
            {"userId": oid, "status": _PENDING, "expiresAt": {"$lte": utcnow()}},
            {"$set": {"status": "EXPIRADO"}},
        )
