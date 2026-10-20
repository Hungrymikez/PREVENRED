"""
Índices de fieldwork (censo de inmuebles e inspecciones). Se crean al arrancar.

- `caseId` único: es el consecutivo que se le dice al ciudadano; repetirlo
  confundiría dos inmuebles distintos.
- `clientId` único PARCIAL (solo si existe): garantiza en la base la idempotencia
  de CU-37 aunque dos envíos offline lleguen a la vez.
- `location` 2dsphere: permite buscar inmuebles por cercanía en el mapa.
"""
from pymongo.database import Database

from prevenred.fieldwork.infrastructure.mongo_inspection_repository import (
    COLLECTION as INSPECTIONS_COLLECTION,
)
from prevenred.fieldwork.infrastructure.mongo_property_repository import (
    COLLECTION as PROPERTIES_COLLECTION,
)


def ensure_indexes(db: Database) -> None:
    """Crea los índices de `properties` y `property_inspections` (idempotente)."""
    properties = db[PROPERTIES_COLLECTION]
    properties.create_index(
        "caseId", unique=True, name="uq_properties_case", sparse=True
    )
    properties.create_index(
        "clientId",
        unique=True,
        name="uq_properties_client",
        partialFilterExpression={"clientId": {"$type": "string"}},
    )
    properties.create_index([("location", "2dsphere")], name="geo_properties_location")
    properties.create_index(
        [("createdBy", 1), ("createdAt", -1)], name="ix_properties_inspector_created"
    )
    properties.create_index("status", name="ix_properties_status")

    inspections = db[INSPECTIONS_COLLECTION]
    inspections.create_index(
        [("propertyId", 1), ("inspectedAt", 1)], name="ix_inspections_property_date"
    )
    inspections.create_index(
        "clientId",
        unique=True,
        name="uq_inspections_client",
        partialFilterExpression={"clientId": {"$type": "string"}},
    )
    inspections.create_index(
        [("requiresSecondReview", 1), ("secondReviewBy", 1)],
        name="ix_inspections_pending_review",
    )
