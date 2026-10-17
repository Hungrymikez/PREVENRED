"""Índices de bienestar (consentimientos y encuestas anónimas). Idempotente."""
from pymongo.database import Database

from prevenred.wellbeing.infrastructure.mongo_wellbeing_repository import CONSENTS, SURVEYS


def ensure_indexes(db: Database) -> None:
    """Crea los índices de `wellbeing_consents` y `wellbeing_surveys` (CU-23, CU-24)."""
    consents = db[CONSENTS]
    # Un único consentimiento vigente por persona y finalidad: evita lecturas
    # ambiguas sobre cuál permiso aplica (los revocados no entran al parcial).
    consents.create_index(
        [("userId", 1), ("purpose", 1)],
        unique=True,
        partialFilterExpression={"granted": True, "revokedAt": None},
        name="uq_consent_active",
    )
    consents.create_index([("userId", 1), ("grantedAt", -1)], name="ix_consent_user_granted")

    surveys = db[SURVEYS]
    # El par pseudónimo+semana ES la regla de "una respuesta por semana" (O-08).
    # El índice único parcial la hace cumplir incluso si dos peticiones llegan
    # a la vez; el servicio igualmente comprueba antes para dar un 409 legible.
    surveys.create_index(
        [("pseudonym", 1), ("weekKey", 1)],
        unique=True,
        name="uq_surveys_pseudonym_week",
    )
    # Índice de lectura para el panel: por zona y fecha, nunca por usuario.
    surveys.create_index([("zone", 1), ("createdAt", -1)], name="ix_surveys_zone_created")
    surveys.create_index([("createdAt", -1)], name="ix_surveys_created")
