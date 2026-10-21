"""Repositorio de modos operacionales sobre MongoDB: colección `operational_modes`."""

from bson import ObjectId
from pymongo.database import Database

from prevenred.operating_mode.domain.mode import OperationalMode, OperationalModeType
from prevenred.operating_mode.domain.repositories import OperationalModeRepository
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "operational_modes"


def _to_entity(doc: dict) -> OperationalMode:
    """Documento Mongo -> entidad de dominio."""
    return OperationalMode(
        id=str(doc["_id"]),
        mode=OperationalModeType(doc["mode"]),
        previous_mode=OperationalModeType(doc["previousMode"]),
        changed_by=str(doc["changedBy"]),
        reason=doc["reason"],
        created_at=as_utc(doc["startedAt"]),
        active=bool(doc.get("active", True)),
        ended_at=as_utc(doc.get("endedAt")),
        mfa_verified=bool(doc.get("mfaVerified", False)),
    )


def _to_document(record: OperationalMode) -> dict:
    """Entidad -> documento Mongo (camelCase, docs/db/operational_modes.md)."""
    return {
        "_id": ObjectId(record.id),
        "mode": record.mode.value,
        "reason": record.reason,
        "changedBy": ObjectId(record.changed_by),
        "previousMode": record.previous_mode.value,
        "startedAt": record.created_at,
        "endedAt": record.ended_at,
        "active": record.active,
        "mfaVerified": record.mfa_verified,
    }


class MongoOperationalModeRepository(OperationalModeRepository):
    """OperationalModeRepository sobre la colección `operational_modes`."""

    def __init__(self, database: Database) -> None:
        self._collection = database[COLLECTION]

    def get_current_mode(self) -> OperationalMode:
        doc = self._collection.find_one({"active": True}, sort=[("startedAt", -1)])
        if doc is None:
            # Sin historial: modo cotidiano por defecto (no se persiste hasta el primer cambio).
            return OperationalMode.default_cotidiano()
        return _to_entity(doc)

    def save(self, mode_record: OperationalMode) -> None:
        now = mode_record.created_at or utcnow()
        # Cierra el modo vigente anterior sin borrarlo (RN-02).
        self._collection.update_many(
            {"active": True},
            {"$set": {"active": False, "endedAt": now}},
        )
        self._collection.insert_one(_to_document(mode_record))
