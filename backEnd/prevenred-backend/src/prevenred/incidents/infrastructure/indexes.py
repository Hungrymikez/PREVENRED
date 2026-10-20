"""
Índices de incidentes. Se crean al arrancar la app (idempotente).

- `caseId` único: consecutivo visible al ciudadano.
- `location` 2dsphere: búsqueda por cercanía para detectar duplicados.
- `clientId` único PARCIAL: idempotencia de la sincronización offline (CU-37).
"""
from pymongo.database import Database


def ensure_indexes(db: Database) -> None:
    """Crea los índices de la colección `incidents`."""
    incidents = db["incidents"]
    incidents.create_index("caseId", unique=True, name="uq_incidents_case", sparse=True)
    incidents.create_index([("location", "2dsphere")], name="geo_incidents_location")
    incidents.create_index(
        [("status", 1), ("priority", -1)], name="ix_incidents_status_priority"
    )
    incidents.create_index(
        [("reportedBy", 1), ("createdAt", -1)], name="ix_incidents_reporter_created"
    )
    incidents.create_index(
        "clientId",
        unique=True,
        name="uq_incidents_client",
        partialFilterExpression={"clientId": {"$type": "string"}},
    )
    # Los duplicados se excluyen del tablero: conviene consultarlos aparte.
    incidents.create_index("duplicateOf", name="ix_incidents_duplicate_of")
