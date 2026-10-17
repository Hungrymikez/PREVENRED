"""
Repositorios de bienestar: `wellbeing_consents` y `wellbeing_surveys` (CU-23/24).

`MongoSurveyRepository.add` escribe un documento CERRADO: no hay mapeo genérico
de la entidad que pudiera arrastrar un `userId` si mañana alguien lo añade. Si
no aparece en ese diccionario, no se guarda.
"""
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)
from prevenred.wellbeing.domain.entities import Consent, SurveyResponse
from prevenred.wellbeing.domain.repositories import ConsentRepository, SurveyRepository

CONSENTS = "wellbeing_consents"
SURVEYS = "wellbeing_surveys"


def _consent_to_entity(d: dict) -> Consent:
    """Documento -> Consent."""
    return Consent(
        id=str(d["_id"]),
        user_id=str(d["userId"]),
        purpose=d["purpose"],
        privacy_notice_version=d.get("privacyNoticeVersion", "1.0"),
        granted=bool(d.get("granted", True)),
        granted_at=utc_aware(d["grantedAt"]),
        revoked_at=utc_aware(d.get("revokedAt")),
    )


class MongoConsentRepository(BaseMongoRepository[Consent], ConsentRepository):
    """ConsentRepository sobre la colección `wellbeing_consents`."""

    collection = CONSENTS

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._consents = self._col

    def to_document(self, c: Consent) -> dict:
        """Consentimiento -> documento completo."""
        return {
            "_id": ObjectId(c.id),
            "userId": to_reference(c.user_id),
            "purpose": c.purpose,
            "privacyNoticeVersion": c.privacy_notice_version,
            "granted": c.granted,
            "grantedAt": c.granted_at,
            "revokedAt": c.revoked_at,
        }

    def to_entity(self, document: dict) -> Consent:
        """Documento -> consentimiento."""
        return _consent_to_entity(document)

    def updates(self, c: Consent) -> dict:
        """Solo cambia la revocación (el consentimiento original no se reescribe)."""
        return {"granted": c.granted, "revokedAt": c.revoked_at}

    def list_by_user(self, user_id: str) -> list[Consent]:
        """Historial de la persona, más reciente primero."""
        oid = to_object_id(user_id)
        if oid is None:
            return []
        cursor = self._consents.find({"userId": oid}).sort("grantedAt", -1)
        return [_consent_to_entity(doc) for doc in cursor]

    def find_active(self, user_id: str, purpose: str) -> Consent | None:
        """Permiso vigente de una finalidad."""
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = self._consents.find_one(
            {"userId": oid, "purpose": purpose, "granted": True, "revokedAt": None}
        )
        return _consent_to_entity(doc) if doc else None



class MongoSurveyRepository(SurveyRepository):
    """SurveyRepository sobre la colección `wellbeing_surveys`.

    No hereda de `BaseMongoRepository` porque una respuesta no se edita ni se
    consulta por id: exponer `update()` invitaría a "corregir" datos anónimos.
    """

    def __init__(self, db: Database) -> None:
        self._surveys = db[SURVEYS]

    def add(self, response: SurveyResponse) -> None:
        """Inserta la respuesta; el documento NO tiene ningún id de persona."""
        self._surveys.insert_one(
            {
                "answers": dict(response.answers),
                "pseudonym": response.pseudonym,
                "weekKey": response.week_key,
                "zone": response.zone,
                "triggerEventId": to_reference(response.trigger_event_id),
                "createdAt": response.created_at,
            }
        )

    def last_response_at(self, pseudonym: str) -> datetime | None:
        """Momento del último envío del mismo pseudónimo (límite semanal)."""
        doc = self._surveys.find_one(
            {"pseudonym": pseudonym}, {"createdAt": 1}, sort=[("createdAt", -1)]
        )
        return utc_aware(doc["createdAt"]) if doc else None

    def count_between(self, start: datetime, end: datetime) -> int:
        """Conteo agregado del periodo (sin identificar a nadie)."""
        return self._surveys.count_documents({"createdAt": {"$gte": start, "$lt": end}})
