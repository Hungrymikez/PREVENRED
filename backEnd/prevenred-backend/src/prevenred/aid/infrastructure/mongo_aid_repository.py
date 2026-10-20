"""
Repositorios de ayuda sobre MongoDB: `aid_needs` y `aid_inventory` (CU-31/41/42).

El punto crítico es `reserve_stock`: primero LEE el disponible, luego escribe con
un FILTRO CONDICIONAL (`availableQuantity >= amount`). El filtro se evalúa dentro
de la escritura, así que si otra entrega tomó el stock en el intermedio, esta
escritura no coincide con ningún documento y devuelve False en lugar de dejar el
inventario en negativo (ver docs/09_rectificacion_bd_mongodb.md §5).
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.aid.domain.entities import AidInventoryItem, AidNeed
from prevenred.aid.domain.repositories import AidInventoryRepository, AidNeedRepository
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

#: Nombre de la colección en snake_case (docs/EQUIVALENCIAS_BD.md, fila 16).
NEEDS_COLLECTION = "aid_needs"
INVENTORY_COLLECTION = "aid_inventory"


# ------------------------------------------------------------ necesidades
def _need_to_entity(d: dict) -> AidNeed:
    """Documento -> AidNeed."""
    point = d.get("location") or {}
    coords = point.get("coordinates") or [None, None]
    return AidNeed(
        id=str(d["_id"]),
        type=d["type"],
        description=d["description"],
        requested_by=str(d["requestedBy"]),
        quantity=int(d.get("quantity") or 1),
        latitude=coords[1],
        longitude=coords[0],
        priority=d.get("priority", "MEDIA"),
        status=d.get("status", "ABIERTA"),
        case_id=d.get("caseId"),
        incident_id=str(d["incidentId"]) if d.get("incidentId") else None,
        covered_quantity=int(d.get("coveredQuantity") or 0),
        created_at=utc_aware(d["createdAt"]),
    )


class MongoAidNeedRepository(BaseMongoRepository[AidNeed], AidNeedRepository):
    """AidNeedRepository sobre la colección `aid_needs`."""
    collection = NEEDS_COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._needs = self._col

    def to_document(self, need: AidNeed) -> dict:
        """Necesidad -> documento completo."""
        location = None
        if need.latitude is not None and need.longitude is not None:
            location = {"type": "Point", "coordinates": [need.longitude, need.latitude]}
        return {
            "_id": ObjectId(need.id),
            "type": need.type,
            "description": need.description,
            "quantity": need.quantity,
            "location": location,
            "priority": need.priority,
            "status": need.status,
            "requestedBy": to_reference(need.requested_by),
            "caseId": need.case_id,
            "incidentId": to_reference(need.incident_id),
            "coveredQuantity": need.covered_quantity,
            "createdAt": need.created_at,
        }

    def to_entity(self, document: dict) -> AidNeed:
        """Documento -> necesidad."""
        return _need_to_entity(document)

    def updates(self, need: AidNeed) -> dict:
        """Cambian el avance de la entrega y el estado."""
        return {
            "coveredQuantity": need.covered_quantity,
            "status": need.status,
        }

    def list_by_requester(self, user_id: str, *, limit: int = 100) -> list[AidNeed]:
        """Necesidades pedidas por la persona, más recientes primero."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        cursor = self._needs.find({"requestedBy": oid}).sort("createdAt", -1).limit(limit)
        return [_need_to_entity(doc) for doc in cursor]

    def list_open(self, *, limit: int = 200) -> list[AidNeed]:
        """Necesidades sin cubrir, prioridad primero (CU-42)."""
        cursor = (
            self._needs.find({"status": {"$in": ["ABIERTA", "PARCIAL"]}})
            .sort([("priority", -1), ("createdAt", 1)])
            .limit(limit)
        )
        return [_need_to_entity(doc) for doc in cursor]


# --------------------------------------------------------------- inventario
def _item_to_entity(d: dict) -> AidInventoryItem:
    """Documento -> AidInventoryItem."""
    return AidInventoryItem(
        id=str(d["_id"]),
        source_id=str(d["sourceId"]),
        source_type=d.get("sourceType", "MATERIAL"),
        type=d["type"],
        quantity=int(d["quantity"]),
        origin_trace=d.get("originTrace", ""),
        available_quantity=int(d.get("availableQuantity") or 0),
        status=d.get("status", "DISPONIBLE"),
        updated_at=utc_aware(d.get("updatedAt")),
        created_at=utc_aware(d["createdAt"]),
    )



class MongoAidInventoryRepository(BaseMongoRepository[AidInventoryItem], AidInventoryRepository):
    """AidInventoryRepository sobre la colección `aid_inventory`."""
    collection = INVENTORY_COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._items = self._col

    def to_document(self, item: AidInventoryItem) -> dict:
        """Recurso -> documento completo."""
        return {
            "_id": ObjectId(item.id),
            "sourceId": to_reference(item.source_id),
            "sourceType": item.source_type,
            "type": item.type,
            "quantity": item.quantity,
            "availableQuantity": item.available_quantity or 0,
            "status": item.status,
            "originTrace": item.origin_trace,
            "createdAt": item.created_at,
            "updatedAt": item.updated_at or item.created_at,
        }

    def to_entity(self, document: dict) -> AidInventoryItem:
        """Documento -> recurso."""
        return _item_to_entity(document)

    def updates(self, item: AidInventoryItem) -> dict:
        """Solo cambian cantidades, estado y trazabilidad (no el origen)."""
        return {
            "quantity": item.quantity,
            "availableQuantity": item.available_quantity or 0,
            "status": item.status,
            "originTrace": item.origin_trace,
            "updatedAt": item.updated_at or utcnow(),
        }

    def reserve_stock(self, item_id: str, amount: int) -> bool:
        """Reserva atómica: el filtro comprueba el stock en el mismo momento de escribir.

        Devuelve False si el recurso no existe, no está DISPONIBLE o ya no alcanza.
        """
        oid = to_object_id(item_id)
        if oid is None or amount <= 0:
            return False
        result = self._items.update_one(
            {
                "_id": oid,
                "status": "DISPONIBLE",
                "availableQuantity": {"$gte": amount},
            },
            {"$inc": {"availableQuantity": -amount}, "$set": {"updatedAt": utcnow()}},
        )
        if result.modified_count != 1:
            return False
        # Quedó en cero -> AGOTADO. Es una segunda escritura condicional: si otra
        # petición repuso stock entre medio, el filtro no coincide y no se marca.
        self._items.update_one(
            {"_id": oid, "availableQuantity": 0}, {"$set": {"status": "AGOTADO"}}
        )
        return True

    def list_available(
        self, *, type: str | None = None, limit: int = 200
    ) -> list[AidInventoryItem]:
        """Recursos con existencias (CU-41)."""
        query: dict = {"status": "DISPONIBLE", "availableQuantity": {"$gt": 0}}
        if type is not None:
            query["type"] = type
        cursor = self._items.find(query).sort("updatedAt", -1).limit(limit)
        return [_item_to_entity(doc) for doc in cursor]
