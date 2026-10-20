"""
Repositorio de inspecciones sobre MongoDB: colección `property_inspections` (CU-35).

La inspección se guarda como documento propio (no dentro del inmueble) porque se
hacen varias visitas al mismo inmueble y cada una debe conservarse como evidencia
del protocolo aplicado (`protocolVersion`).
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.fieldwork.domain.entities import Inspection
from prevenred.fieldwork.domain.repositories import InspectionRepository
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "property_inspections"


def _to_entity(d: dict) -> Inspection:
    """Documento -> Inspection."""
    return Inspection(
        id=str(d["_id"]),
        property_id=str(d["propertyId"]),
        inspector_id=str(d["inspectorId"]),
        damage_level=d["damageLevel"],
        habitability_status=d["habitabilityStatus"],
        findings=d.get("findings") or "",
        evidence_files=tuple(str(e) for e in d.get("evidenceFiles") or ()),
        protocol_version=d.get("protocolVersion", "1"),
        inspected_at=utc_aware(d["inspectedAt"]),
        client_id=d.get("clientId"),
        synced_at=utc_aware(d.get("syncedAt")),
        second_review_by=str(d["secondReviewBy"]) if d.get("secondReviewBy") else None,
        created_at=utc_aware(d.get("createdAt") or d["inspectedAt"]),
    )


def _to_document(i: Inspection) -> dict:
    """Inspection -> documento completo."""
    return {
        "_id": ObjectId(i.id),
        "propertyId": to_reference(i.property_id),
        "inspectorId": to_reference(i.inspector_id),
        "damageLevel": i.damage_level,
        "habitabilityStatus": i.habitability_status,
        "findings": i.findings,
        "evidenceFiles": [to_reference(e) for e in i.evidence_files],
        "protocolVersion": i.protocol_version,
        "inspectedAt": i.inspected_at,
        "clientId": i.client_id,
        "syncedAt": i.synced_at,
        "requiresSecondReview": i.requires_second_review,
        "secondReviewBy": to_reference(i.second_review_by),
        "createdAt": i.created_at,
    }


class MongoInspectionRepository(BaseMongoRepository[Inspection], InspectionRepository):
    """InspectionRepository sobre la colección `property_inspections`."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._inspections = self._col

    def to_document(self, inspection: Inspection) -> dict:
        """Inspección -> documento completo."""
        return _to_document(inspection)

    def to_entity(self, document: dict) -> Inspection:
        """Documento -> inspección."""
        return _to_entity(document)

    def updates(self, inspection: Inspection) -> dict:
        """Solo cambia la segunda revisión de un caso crítico."""
        return {
            "requiresSecondReview": inspection.requires_second_review,
            "secondReviewBy": to_reference(inspection.second_review_by),
            "syncedAt": inspection.synced_at,
        }

    def get_by_client_id(self, client_id: str) -> Inspection | None:
        """Busca por el id generado en el celular (CU-37)."""
        doc = self._inspections.find_one({"clientId": client_id})
        return _to_entity(doc) if doc else None

    def list_by_property(self, property_id: str) -> list[Inspection]:
        """Historial de inspecciones del inmueble, de la más antigua a la más nueva."""
        oid = to_object_id(property_id)
        if oid is None:
            return []
        cursor = self._inspections.find({"propertyId": oid}).sort("inspectedAt", 1)
        return [_to_entity(doc) for doc in cursor]

    def list_pending_second_review(self, *, limit: int = 100) -> list[Inspection]:
        """Casos críticos sin segundo revisor (O-11)."""
        cursor = (
            self._inspections.find(
                {"requiresSecondReview": True, "secondReviewBy": None},
            )
            .sort("inspectedAt", 1)
            .limit(limit)
        )
        return [_to_entity(doc) for doc in cursor]
