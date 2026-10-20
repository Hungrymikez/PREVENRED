"""
Repositorio de avisos sobre MongoDB: colección `notifications` (CU-06, CU-07).

Los avisos de zona se insertan por lote con `insert_many`: si hay 500 vecinos,
500 escrituras individuales tardarían demasiado; una sola operación es más rápida
y no deja el aviso "a medias".
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.notifications.domain.notification import MAX_ATTEMPTS, Notification
from prevenred.notifications.domain.repositories import NotificationRepository
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "notifications"


def _to_entity(d: dict) -> Notification:
    """Documento -> Notification."""
    return Notification(
        id=str(d["_id"]),
        user_id=str(d["userId"]),
        channel=d["channel"],
        title=d["title"],
        message=d["message"],
        type=d.get("type", "OTRO"),
        zone=d.get("zone") or "",
        status=d.get("status", "PENDIENTE"),
        attempts=int(d.get("attempts") or 0),
        sent_at=utc_aware(d.get("sentAt")),
        last_error=d.get("lastError"),
        read_at=utc_aware(d.get("readAt")),
        created_at=utc_aware(d["createdAt"]),
    )


def _to_document(n: Notification) -> dict:
    """Notification -> documento completo."""
    return {
        "_id": ObjectId(n.id),
        "userId": to_reference(n.user_id),
        "channel": n.channel,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "zone": n.zone,
        "status": n.status,
        "attempts": n.attempts,
        "sentAt": n.sent_at,
        "lastError": n.last_error,
        "readAt": n.read_at,
        "createdAt": n.created_at,
    }


class MongoNotificationRepository(BaseMongoRepository[Notification], NotificationRepository):
    """NotificationRepository sobre la colección `notifications`."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._notifications = self._col

    def to_document(self, notification: Notification) -> dict:
        """Aviso -> documento completo."""
        return _to_document(notification)

    def to_entity(self, document: dict) -> Notification:
        """Documento -> aviso."""
        return _to_entity(document)

    def updates(self, notification: Notification) -> dict:
        """Cambian el estado de entrega, los reintentos y la lectura."""
        return {
            "status": notification.status,
            "attempts": notification.attempts,
            "sentAt": notification.sent_at,
            "lastError": notification.last_error,
            "readAt": notification.read_at,
        }

    def add_many(self, notifications: list[Notification]) -> None:
        """Inserta un lote de avisos (aviso de crisis a una zona)."""
        if not notifications:
            return
        self._notifications.insert_many([_to_document(n) for n in notifications])

    def list_by_user(
        self, user_id: str, *, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        """Campanita del usuario (CU-07), más recientes primero."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        query: dict = {"userId": oid}
        if unread_only:
            query["readAt"] = None
        cursor = self._notifications.find(query).sort("createdAt", -1).limit(limit)
        return [_to_entity(doc) for doc in cursor]

    def list_pending(self, *, limit: int = 200) -> list[Notification]:
        """Avisos sin entregar: los recoge el reintento del servicio de envío."""
        cursor = (
            self._notifications.find(
                {"status": {"$ne": "ENVIADO"}, "attempts": {"$lt": MAX_ATTEMPTS}}
            )
            .sort("createdAt", 1)
            .limit(limit)
        )
        return [_to_entity(doc) for doc in cursor]
