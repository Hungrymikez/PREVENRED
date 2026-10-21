"""Índices de la colección `incidents` (docs/db/incidents.md)."""

from pymongo import ASCENDING, GEOSPHERE
from pymongo.database import Database

from .mongo_incident_repository import COLLECTION


def ensure_indexes(db: Database) -> None:
    """Crea índices idempotentes: case_number y caseId únicos (sparse), 2dsphere y status."""
    col = db[COLLECTION]

    # Elimina índices legacy o no-sparse para permitir migración limpia a sparse=True
    try:
        idx_info = col.index_information()
        for idx_name in ("case_number_1", "uq_incidents_case_number", "uq_incidents_caseId"):
            if idx_name in idx_info:
                if not idx_info[idx_name].get("sparse", False):
                    col.drop_index(idx_name)
    except Exception:
        pass

    col.create_index("case_number", unique=True, sparse=True, name="uq_incidents_case_number")
    col.create_index("caseId", unique=True, sparse=True, name="uq_incidents_caseId")
    col.create_index([("location", GEOSPHERE)], name="ix_incidents_location_2dsphere")
    col.create_index(
        [("status", ASCENDING), ("severity", ASCENDING)],
        name="ix_incidents_status_severity",
    )
    col.create_index(
        [("reportedBy", ASCENDING), ("createdAt", ASCENDING)],
        name="ix_incidents_reportedBy_createdAt",
    )
