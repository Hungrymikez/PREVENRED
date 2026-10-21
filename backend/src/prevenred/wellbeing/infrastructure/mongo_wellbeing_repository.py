"""Implementación MongoDB del repositorio de bienestar emocional."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.shared.domain.ids import EntityId

from ..domain.consent import WellbeingConsent
from ..domain.repositories import WellbeingRepository
from ..domain.survey import WellbeingSurvey


class MongoWellbeingRepository(WellbeingRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._consents = database["wellbeing_consents"]
        self._surveys = database["wellbeing_surveys"]

    async def create_indexes(self) -> None:
        await self._consents.create_index("user_id", unique=True)
        await self._surveys.create_index("neighborhood")
        await self._surveys.create_index("created_at")

    async def save_consent(self, consent: WellbeingConsent) -> None:
        # Un consentimiento por usuario. El _id es inmutable en MongoDB: solo se fija al
        # insertar; renovar el consentimiento actualiza los demás campos del mismo documento.
        fields = {
            "terms_version": consent.terms_version,
            "consented_at": consent.consented_at,
            "is_revoked": consent.is_revoked,
        }
        await self._consents.update_one(
            {"user_id": consent.user_id.value},
            {"$set": fields, "$setOnInsert": {"_id": consent.id.value}},
            upsert=True,
        )

    async def get_consent_by_user_id(self, user_id: EntityId) -> WellbeingConsent | None:
        uid = user_id.value
        doc = await self._consents.find_one({"user_id": uid})
        if not doc:
            return None
        return WellbeingConsent(
            id=EntityId(str(doc["_id"])),
            user_id=EntityId(str(doc["user_id"])),
            terms_version=doc["terms_version"],
            consented_at=doc["consented_at"],
            is_revoked=bool(doc["is_revoked"]),
        )

    async def save_survey(self, survey: WellbeingSurvey) -> None:
        survey_id = survey.id.value
        user_id = survey.user_id.value
        doc = {
            "_id": survey_id,
            "user_id": user_id,
            "neighborhood": survey.neighborhood,
            "mood_score": survey.mood_score,
            "sanitized_text": survey.sanitized_text,
            "crisis_flag": survey.crisis_flag,
            "created_at": survey.created_at,
        }
        await self._surveys.replace_one({"_id": survey_id}, doc, upsert=True)

    async def get_all_neighborhood_averages(self, min_samples: int = 3) -> list[dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$neighborhood",
                    "sample_count": {"$sum": 1},
                    "average_mood": {"$avg": "$mood_score"},
                    "crisis_count": {"$sum": {"$cond": ["$crisis_flag", 1, 0]}},
                }
            },
            {"$match": {"sample_count": {"$gte": min_samples}}},
            {"$sort": {"sample_count": -1}},
        ]
        results = await self._surveys.aggregate(pipeline).to_list(length=100)
        return [
            {
                "neighborhood": r["_id"],
                "sample_count": r["sample_count"],
                "average_mood": round(r["average_mood"], 2),
                "crisis_alerts": r["crisis_count"],
            }
            for r in results
        ]
