"""Repositorio de incidentes sobre MongoDB: colección `incidents`."""

from typing import Any

from bson import ObjectId
from pymongo.database import Database

from prevenred.incidents.domain.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentStatusTransition,
    IncidentType,
)
from prevenred.incidents.domain.repositories import IncidentRepository
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import as_utc

COLLECTION = "incidents"


def _to_document(incident: Incident) -> dict[str, Any]:
    """Entidad -> documento Mongo (soporta camelCase y snake_case para compatibilidad total)."""
    oid = ObjectId(incident.id) if ObjectId.is_valid(incident.id) else incident.id
    reported_by_oid = (
        ObjectId(incident.reported_by)
        if ObjectId.is_valid(incident.reported_by)
        else incident.reported_by
    )
    assigned_to_oid = None
    if incident.assigned_to:
        assigned_to_oid = (
            ObjectId(incident.assigned_to)
            if ObjectId.is_valid(incident.assigned_to)
            else incident.assigned_to
        )

    return {
        "_id": oid,
        "case_number": incident.case_number,
        "caseId": incident.case_number,
        "type": incident.incident_type.value,
        "incident_type": incident.incident_type.value,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "description": incident.description,
        "location": {
            "type": "Point",
            "coordinates": [incident.longitude, incident.latitude],
        },
        "reportedBy": reported_by_oid,
        "reported_by": reported_by_oid,
        "assignedTo": assigned_to_oid,
        "assigned_to": assigned_to_oid,
        "photos": list(incident.media_urls),
        "media_urls": list(incident.media_urls),
        "history": [
            {
                "previousStatus": h.previous_status.value,
                "previous_status": h.previous_status.value,
                "newStatus": h.new_status.value,
                "new_status": h.new_status.value,
                "changedBy": h.changed_by,
                "changed_by": h.changed_by,
                "changedAt": h.changed_at,
                "changed_at": h.changed_at,
                "notes": h.notes,
            }
            for h in incident.history
        ],
        "createdAt": incident.created_at,
        "created_at": incident.created_at,
        "updatedAt": incident.updated_at or incident.created_at,
        "updated_at": incident.updated_at or incident.created_at,
    }


def _to_entity(doc: dict[str, Any]) -> Incident:
    """Documento Mongo -> entidad de dominio (tolerante a camelCase y snake_case)."""
    loc = doc.get("location") or {}
    coords = loc.get("coordinates") if isinstance(loc, dict) else [0.0, 0.0]
    if not coords or len(coords) < 2:
        coords = [0.0, 0.0]

    history = [
        IncidentStatusTransition(
            previous_status=IncidentStatus(h.get("previousStatus") or h.get("previous_status")),
            new_status=IncidentStatus(h.get("newStatus") or h.get("new_status")),
            changed_by=str(h.get("changedBy") or h.get("changed_by")),
            changed_at=as_utc(h.get("changedAt") or h.get("changed_at")),
            notes=h.get("notes", ""),
        )
        for h in doc.get("history", [])
    ]
    assigned = doc.get("assignedTo") or doc.get("assigned_to")
    case_num = doc.get("case_number") or doc.get("caseId") or doc.get("caseNumber") or ""
    inc_type = doc.get("type") or doc.get("incident_type")
    severity = doc.get("severity")
    status = doc.get("status")
    description = doc.get("description", "")
    reported_by = doc.get("reportedBy") or doc.get("reported_by")
    photos = doc.get("photos") or doc.get("media_urls") or []
    created_at = doc.get("createdAt") or doc.get("created_at") or utcnow()
    updated_at = doc.get("updatedAt") or doc.get("updated_at")

    return Incident(
        id=str(doc["_id"]),
        case_number=case_num,
        incident_type=IncidentType(inc_type),
        severity=IncidentSeverity(severity),
        status=IncidentStatus(status),
        description=description,
        longitude=float(coords[0]),
        latitude=float(coords[1]),
        reported_by=str(reported_by),
        media_urls=list(photos),
        created_at=as_utc(created_at),
        history=history,
        assigned_to=str(assigned) if assigned else None,
        updated_at=as_utc(updated_at) if updated_at else None,
    )


class MongoIncidentRepository(IncidentRepository):
    """IncidentRepository sobre la colección `incidents`."""

    def __init__(self, database: Database) -> None:
        self._collection = database[COLLECTION]

    def save(self, incident: Incident) -> None:
        if incident.updated_at is None:
            incident.updated_at = utcnow()
        doc = _to_document(incident)
        self._collection.replace_one(
            {"_id": doc["_id"]},
            doc,
            upsert=True,
        )

    def get_by_id(self, incident_id: EntityId) -> Incident | None:
        oid = ObjectId(incident_id) if ObjectId.is_valid(incident_id) else incident_id
        doc = self._collection.find_one({"_id": oid})
        return _to_entity(doc) if doc else None

    def list_recent(
        self,
        status: IncidentStatus | None = None,
        limit: int = 50,
    ) -> list[Incident]:
        query: dict[str, Any] = {}
        if status is not None:
            query["status"] = status.value
        cursor = self._collection.find(query).sort("createdAt", -1).limit(limit)
        return [_to_entity(doc) for doc in cursor]
