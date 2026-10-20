"""
Repositorio de reportes sobre MongoDB: colección `incidents` (CU-29/30/32/39).

Decisiones:
  - `inspections` es un ARREGLO dentro del reporte: se alimenta con `$push` para
    que dos registros simultáneos no se pisen (ver domain/repositories.py).
  - `duplicateOf` guarda el reporte principal; los duplicados se excluyen del
    conteo del tablero, no se borran.
  - `location` es GeoJSON Point para la búsqueda por cercanía (`$geoNear`), que
    alimenta la detección de duplicados.
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.incidents.domain.incident import Incident
from prevenred.incidents.domain.repositories import IncidentRepository
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "incidents"


def _to_entity(d: dict) -> Incident:
    """Documento -> Incident (las fotos e inspecciones se leen aquí)."""
    point = (d.get("location") or {}).get("coordinates") or [0.0, 0.0]
    return Incident(
        id=str(d["_id"]),
        type=d["type"],
        description=d["description"],
        latitude=float(point[1]),
        longitude=float(point[0]),
        reported_by=str(d["reportedBy"]),
        status=d.get("status", "REPORTADO"),
        priority=d.get("priority", "MEDIA"),
        severity=d.get("severity", "MODERADA"),
        needs=tuple(d.get("needs") or ()),
        photos=tuple(str(p) for p in d.get("photos") or ()),
        assigned_to=str(d["assignedTo"]) if d.get("assignedTo") else None,
        case_id=d.get("caseId"),
        reported_at=utc_aware(d.get("reportedAt")),
        client_id=d.get("clientId"),
        duplicate_of=str(d["duplicateOf"]) if d.get("duplicateOf") else None,
        property_id=str(d["propertyId"]) if d.get("propertyId") else None,
        updated_at=utc_aware(d.get("updatedAt")),
        created_at=utc_aware(d["createdAt"]),
    )


def _to_document(i: Incident) -> dict:
    """Incident -> documento completo."""
    return {
        "_id": ObjectId(i.id),
        "caseId": i.case_id,
        "type": i.type,
        "description": i.description,
        "location": {"type": "Point", "coordinates": [i.longitude, i.latitude]},
        "photos": [to_reference(p) for p in i.photos],
        "status": i.status,
        "priority": i.priority,
        "severity": i.severity,
        "needs": list(i.needs),
        "reportedBy": to_reference(i.reported_by),
        "assignedTo": to_reference(i.assigned_to),
        "reportedAt": i.reported_at,
        "clientId": i.client_id,
        "duplicateOf": to_reference(i.duplicate_of),
        "propertyId": to_reference(i.property_id),
        "inspections": [],      # se llenan con $push (append_inspection)
        "createdAt": i.created_at,
        "updatedAt": i.updated_at or i.created_at,
    }


class MongoIncidentRepository(BaseMongoRepository[Incident], IncidentRepository):
    """IncidentRepository sobre la colección `incidents`."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._incidents = self._col

    def to_document(self, incident: Incident) -> dict:
        """Reporte -> documento completo."""
        return _to_document(incident)

    def to_entity(self, document: dict) -> Incident:
        """Documento -> reporte."""
        return _to_entity(document)

    def updates(self, incident: Incident) -> dict:
        """Campos que cambian al gestionar el reporte (nunca la ubicación ni el tipo)."""
        return {
            "caseId": incident.case_id,
            "status": incident.status,
            "priority": incident.priority,
            "assignedTo": to_reference(incident.assigned_to),
            "duplicateOf": to_reference(incident.duplicate_of),
            "photos": [to_reference(p) for p in incident.photos],
            "updatedAt": incident.updated_at,
        }

    # ---- Consultas del contexto ----
    def get_by_client_id(self, client_id: str) -> Incident | None:
        """Busca por el id generado en el celular (CU-37)."""
        doc = self._incidents.find_one({"clientId": client_id})
        return _to_entity(doc) if doc else None

    def list_by_reporter(self, user_id: str, *, limit: int = 100) -> list[Incident]:
        """'Mis casos' (CU-32): reportes de la persona, más recientes primero."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        cursor = self._incidents.find({"reportedBy": oid}).sort("createdAt", -1).limit(limit)
        return [_to_entity(doc) for doc in cursor]

    def list_active(self, *, limit: int = 200) -> list[Incident]:
        """Reportes sin cerrar y sin marcar como duplicado (tablero del coordinador).

        Excluir los duplicados es lo que evita inflar los indicadores.
        """
        cursor = (
            self._incidents.find({"status": {"$ne": "CERRADO"}, "duplicateOf": None})
            .sort([("priority", -1), ("createdAt", 1)])
            .limit(limit)
        )
        return [_to_entity(doc) for doc in cursor]

    def list_duplicates_of(self, primary_id: str) -> list[Incident]:
        """Reportes que se marcaron como duplicados de uno principal (CU-30)."""
        oid = to_object_id(primary_id)
        if oid is None:
            return []
        return [_to_entity(doc) for doc in self._incidents.find({"duplicateOf": oid})]

    def list_nearby(
        self, latitude: float, longitude: float, radius_m: int, *, limit: int = 50
    ) -> list[Incident]:
        """Candidatos a duplicado cerca de un punto (detección de duplicados).

        Usa `$geoNear` con el índice 2dsphere y mide en metros. mongomock NO lo
        soporta: las pruebas de este método usan el fixture `real_db`.
        """
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [longitude, latitude]},
                    "distanceField": "_distanceMeters",
                    "maxDistance": radius_m,
                    "spherical": True,
                }
            },
            {"$match": {"duplicateOf": None}},
            {"$limit": limit},
        ]
        return [_to_entity(doc) for doc in self._incidents.aggregate(pipeline)]

    def append_inspection(self, incident_id: str, inspection: dict) -> bool:
        """Agrega una inspección con `$push` (atómico: no pisa las de otros).

        La inspección es un documento EMBEBIDO: pertenece al reporte y no tiene
        sentido fuera de él, así que no necesita colección propia.
        """
        oid = to_object_id(incident_id)
        if oid is None:
            return False
        result = self._incidents.update_one(
            {"_id": oid},
            {"$push": {"inspections": inspection}, "$set": {"updatedAt": inspection["createdAt"]}},
        )
        return result.matched_count == 1

