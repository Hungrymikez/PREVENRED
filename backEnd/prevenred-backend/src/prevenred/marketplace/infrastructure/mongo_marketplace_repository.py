"""
Repositorios del marketplace: `reservations` y `transactions` (CU-13/14/15).

La detección de choques de fechas usa dos condiciones (`startDate < fin pedido` y
`endDate > inicio pedido`), que el índice compuesto `toolId+startDate+endDate`
resuelve sin traer todas las reservas de la herramienta.
"""
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from prevenred.marketplace.domain.entities import (
    BLOCKING_STATUSES,
    Reservation,
    ToolTransaction,
)
from prevenred.marketplace.domain.repositories import (
    ReservationRepository,
    TransactionRepository,
)
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

RESERVATIONS = "reservations"
TRANSACTIONS = "transactions"   # antes `toolTransactions` (docs/EQUIVALENCIAS_BD.md, fila 11)


def _reservation_to_entity(d: dict) -> Reservation:
    """Documento -> Reservation."""
    return Reservation(
        id=str(d["_id"]),
        tool_id=str(d["toolId"]),
        requester_id=str(d["requesterId"]),
        owner_id=str(d["ownerId"]),
        start_date=utc_aware(d["startDate"]),
        end_date=utc_aware(d["endDate"]),
        cost=float(d.get("cost") or 0),
        status=d.get("status", "SOLICITADA"),
        returned_at=utc_aware(d.get("returnedAt")),
        created_at=utc_aware(d["createdAt"]),
    )


class MongoReservationRepository(BaseMongoRepository[Reservation], ReservationRepository):
    """ReservationRepository sobre la colección `reservations`."""
    collection = RESERVATIONS

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._reservations = self._col

    def to_document(self, r: Reservation) -> dict:
        """Reserva -> documento completo."""
        return {
            "_id": ObjectId(r.id),
            "toolId": to_reference(r.tool_id),
            "requesterId": to_reference(r.requester_id),
            "ownerId": to_reference(r.owner_id),
            "startDate": r.start_date,
            "endDate": r.end_date,
            "cost": r.cost,
            "status": r.status,
            "returnedAt": r.returned_at,
            "createdAt": r.created_at,
        }

    def to_entity(self, document: dict) -> Reservation:
        """Documento -> reserva."""
        return _reservation_to_entity(document)

    def updates(self, r: Reservation) -> dict:
        """Cambian el estado y la devolución; las fechas no se mueven."""
        return {"status": r.status, "returnedAt": r.returned_at}

    def list_by_requester(self, user_id: str, *, limit: int = 100) -> list[Reservation]:
        """'Mis reservas' (CU-14), más recientes primero."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        cursor = self._reservations.find({"requesterId": oid}).sort("createdAt", -1).limit(limit)
        return [_reservation_to_entity(doc) for doc in cursor]

    def list_by_owner(self, user_id: str, *, limit: int = 100) -> list[Reservation]:
        """Solicitudes recibidas (CU-13), más recientes primero."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        cursor = self._reservations.find({"ownerId": oid}).sort("createdAt", -1).limit(limit)
        return [_reservation_to_entity(doc) for doc in cursor]

    def list_blocking_between(
        self, tool_id: str, start: datetime, end: datetime
    ) -> list[Reservation]:
        """Reservas activas que se cruzan con el rango pedido.

        Dos rangos se cruzan si una empieza antes de que termine la otra y
        termina después de que empiece la otra.
        """
        oid = to_object_id(tool_id)
        if oid is None:
            return []
        cursor = self._reservations.find(
            {
                "toolId": oid,
                "status": {"$in": list(BLOCKING_STATUSES)},
                "startDate": {"$lt": end},
                "endDate": {"$gt": start},
            }
        )
        return [_reservation_to_entity(doc) for doc in cursor]



class MongoTransactionRepository(BaseMongoRepository[ToolTransaction], TransactionRepository):
    """TransactionRepository sobre la colección `transactions`."""
    collection = TRANSACTIONS

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._transactions = self._col

    def to_document(self, t: ToolTransaction) -> dict:
        """Operación -> documento completo."""
        return {
            "_id": ObjectId(t.id),
            "buyerId": to_reference(t.buyer_id),
            "sellerId": to_reference(t.seller_id),
            "itemId": to_reference(t.item_id),
            "type": t.type,
            "amount": t.amount,
            "status": t.status,
            "completedAt": t.completed_at,
            "createdAt": t.created_at,
        }

    def to_entity(self, document: dict) -> ToolTransaction:
        """Documento -> operación."""
        d = document
        return ToolTransaction(
            id=str(d["_id"]),
            buyer_id=str(d["buyerId"]),
            seller_id=str(d["sellerId"]),
            item_id=str(d["itemId"]),
            type=d["type"],
            amount=float(d.get("amount") or 0),
            status=d.get("status", "SOLICITADA"),
            completed_at=utc_aware(d.get("completedAt")),
            created_at=utc_aware(d["createdAt"]),
        )

    def updates(self, t: ToolTransaction) -> dict:
        """Cambian el estado y la fecha de finalización."""
        return {"status": t.status, "completedAt": t.completed_at}

    def list_by_participant(self, user_id: str, *, limit: int = 100) -> list[ToolTransaction]:
        """Operaciones donde la persona compró o vendió."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        cursor = (
            self._transactions.find({"$or": [{"buyerId": oid}, {"sellerId": oid}]})
            .sort("createdAt", -1)
            .limit(limit)
        )
        return [self.to_entity(doc) for doc in cursor]
