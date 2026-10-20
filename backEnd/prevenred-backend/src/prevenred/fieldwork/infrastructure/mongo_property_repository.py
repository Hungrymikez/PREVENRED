"""
Repositorio de inmuebles sobre MongoDB: colección `properties` (CU-34, CU-37).

La ubicación se guarda como GeoJSON Point para que el mapa pueda buscar por
proximidad (índice 2dsphere, `$geoNear`). El `clientId` del celular es único
cuando existe: dos envíos del mismo censo offline no crean dos inmuebles.
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.fieldwork.domain.entities import Property
from prevenred.fieldwork.domain.repositories import PropertyRepository
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "properties"


def _to_entity(d: dict) -> Property:
    """Documento -> Property (lat/long salen del GeoJSON)."""
    point = (d.get("location") or {}).get("coordinates") or [0.0, 0.0]
    return Property(
        id=str(d["_id"]),
        address=d["address"],
        latitude=float(point[1]),
        longitude=float(point[0]),
        created_by=str(d["createdBy"]),
        residents_count=int(d.get("residentsCount") or 0),
        characteristics=d.get("characteristics") or {},
        photos=tuple(str(p) for p in d.get("photos") or ()),
        status=d.get("status", "REGISTRADA"),
        case_id=d.get("caseId"),
        client_id=d.get("clientId"),
        synced_at=utc_aware(d.get("syncedAt")),
        created_at=utc_aware(d["createdAt"]),
    )


def _to_document(p: Property) -> dict:
    """Property -> documento completo (GeoJSON exige [longitud, latitud])."""
    return {
        "_id": ObjectId(p.id),
        "caseId": p.case_id,
        "address": p.address,
        "location": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
        "characteristics": p.characteristics,
        "residentsCount": p.residents_count,
        "photos": [to_reference(photo) for photo in p.photos],
        "status": p.status,
        "createdBy": to_reference(p.created_by),
        "clientId": p.client_id,
        "syncedAt": p.synced_at,
        "createdAt": p.created_at,
    }


class MongoPropertyRepository(BaseMongoRepository[Property], PropertyRepository):
    """PropertyRepository sobre la colección `properties`."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._properties = self._col

    def to_document(self, property: Property) -> dict:
        """Inmueble -> documento completo."""
        return _to_document(property)

    def to_entity(self, document: dict) -> Property:
        """Documento -> inmueble."""
        return _to_entity(document)

    def updates(self, property: Property) -> dict:
        """Campos que cambian en el censo (no se reescribe la ubicación: no cambia)."""
        return {
            "caseId": property.case_id,
            "status": property.status,
            "photos": [to_reference(photo) for photo in property.photos],
            "residentsCount": property.residents_count,
            "characteristics": property.characteristics,
            "syncedAt": property.synced_at,
        }

    def get_by_client_id(self, client_id: str) -> Property | None:
        """Busca por el id generado en el celular (CU-37)."""
        doc = self._properties.find_one({"clientId": client_id})
        return _to_entity(doc) if doc else None

    def list_by_inspector(self, inspector_id: str, *, limit: int = 100) -> list[Property]:
        """Inmuebles censados por una persona, más recientes primero."""
        oid = to_object_id(inspector_id)
        if oid is None:
            return []
        cursor = self._properties.find({"createdBy": oid}).sort("createdAt", -1).limit(limit)
        return [_to_entity(doc) for doc in cursor]
