"""Índices de servicios (perfiles de técnico). Se crean al arrancar (idempotente)."""
from pymongo.database import Database


def ensure_indexes(db: Database) -> None:
    """Crea los índices de `technicians` (CU-17, CU-18, CU-19)."""
    technicians = db["technicians"]
    technicians.create_index("userId", unique=True, name="uq_technicians_user")
    technicians.create_index(
        [("specialties", 1), ("verificationStatus", 1)],
        name="ix_technicians_specialty_status",
    )
    # Cola de verificación: pendientes por antigüedad (CU-18).
    technicians.create_index(
        [("verificationStatus", 1), ("createdAt", 1)], name="ix_technicians_status_created"
    )
    # Ranking de la búsqueda pública entre los ya verificados (CU-19).
    technicians.create_index(
        [("verificationStatus", 1), ("rating", -1)], name="ix_technicians_verified_rating"
    )
