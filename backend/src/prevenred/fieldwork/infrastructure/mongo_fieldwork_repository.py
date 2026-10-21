"""Repositorio de inspecciones sobre MongoDB: colección `property_inspections`."""

from typing import Any

from bson import ObjectId
from pymongo.database import Database

from prevenred.fieldwork.domain.inspection import (
    DamageLevel,
    HabitabilityStatus,
    PropertyInspection,
)
from prevenred.fieldwork.domain.repositories import FieldworkRepository
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "property_inspections"


def _to_document(inspection: PropertyInspection) -> dict[str, Any]:
    """Entidad -> documento Mongo (camelCase + GeoJSON Point)."""
    return {
        "_id": ObjectId(inspection.id),
        "propertyAddress": inspection.property_address,
        "neighborhood": inspection.neighborhood,
        "residentsCount": inspection.residents_count,
        "damageLevel": inspection.damage_level.value,
        "habitabilityStatus": inspection.habitability.value,
        "findings": inspection.technical_notes,
        "location": {
            "type": "Point",
            "coordinates": [inspection.longitude, inspection.latitude],
        },
        "inspectorId": ObjectId(inspection.inspector_id),
        "evidenceFiles": list(inspection.photos),
        "inspectedAt": inspection.created_at,
        "syncedAt": inspection.created_at,
    }


def _to_entity(doc: dict[str, Any]) -> PropertyInspection:
    """Documento Mongo -> entidad de dominio."""
    coords = doc["location"]["coordinates"]
    return PropertyInspection(
        id=str(doc["_id"]),
        property_address=doc["propertyAddress"],
        neighborhood=doc["neighborhood"],
        residents_count=int(doc["residentsCount"]),
        damage_level=DamageLevel(doc["damageLevel"]),
        habitability=HabitabilityStatus(doc["habitabilityStatus"]),
        technical_notes=doc.get("findings", ""),
        longitude=float(coords[0]),
        latitude=float(coords[1]),
        inspector_id=str(doc["inspectorId"]),
        photos=list(doc.get("evidenceFiles") or []),
        created_at=as_utc(doc["inspectedAt"]),
    )


class MongoFieldworkRepository(FieldworkRepository):
    """FieldworkRepository sobre la colección `property_inspections`."""

    def __init__(self, database: Database) -> None:
        self._collection = database[COLLECTION]

    def save(self, inspection: PropertyInspection) -> None:
        self._collection.replace_one(
            {"_id": ObjectId(inspection.id)},
            _to_document(inspection),
            upsert=True,
        )

    def get_by_id(self, inspection_id: EntityId) -> PropertyInspection | None:
        doc = self._collection.find_one({"_id": ObjectId(inspection_id)})
        return _to_entity(doc) if doc else None

    def list_by_inspector(self, inspector_id: EntityId) -> list[PropertyInspection]:
        cursor = self._collection.find({"inspectorId": ObjectId(inspector_id)}).sort(
            "inspectedAt", -1
        )
        return [_to_entity(doc) for doc in cursor]
