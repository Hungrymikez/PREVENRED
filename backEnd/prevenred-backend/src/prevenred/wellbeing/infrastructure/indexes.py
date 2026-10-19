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
    # Límite de 1 encuesta por semana (O-08): la semana vive en el consentimiento,
    # no en la encuesta, porque la encuesta es anónima.
    consents.create_index(
        [("userId", 1), ("lastSurveyWeekKey", 1)], name="ix_consent_user_survey_week"
    )

    surveys = db[SURVEYS]
    # La encuesta NO tiene índice por persona: es anónima. Sólo lecturas del panel,
    # por zona y fecha (nunca por usuario).
    surveys.create_index([("zone", 1), ("createdAt", -1)], name="ix_surveys_zone_created")
    surveys.create_index([("createdAt", -1)], name="ix_surveys_created")
