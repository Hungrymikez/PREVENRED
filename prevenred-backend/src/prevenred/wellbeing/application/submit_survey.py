"""Casos de uso para registro de consentimiento y envío de encuestas de bienestar."""

from dataclasses import dataclass
from typing import Any

from prevenred.identity.domain.user import User
from prevenred.shared.domain.errors import AuthorizationError
from prevenred.shared.domain.ids import EntityId

from ..domain.consent import WellbeingConsent
from ..domain.repositories import WellbeingRepository
from ..domain.survey import WellbeingSurvey


@dataclass(frozen=True)
class GrantConsentCommand:
    terms_version: str
    user: User


@dataclass(frozen=True)
class SubmitSurveyCommand:
    neighborhood: str
    mood_score: int
    raw_text: str | None
    user: User


@dataclass(frozen=True)
class SurveyResult:
    survey_id: str
    crisis_detected: bool
    crisis_support_message: str | None
    neighborhood: str
    mood_score: int


class WellbeingUseCase:
    def __init__(self, repository: WellbeingRepository) -> None:
        self._repository = repository

    async def grant_consent(self, command: GrantConsentCommand) -> WellbeingConsent:
        user_id = EntityId(command.user.id)
        consent = WellbeingConsent.create(
            user_id=user_id,
            terms_version=command.terms_version,
        )
        await self._repository.save_consent(consent)
        return consent

    async def submit_survey(self, command: SubmitSurveyCommand) -> SurveyResult:
        # RF-14, RN-05: Exigir consentimiento expreso previo
        user_id = EntityId(command.user.id)
        consent = await self._repository.get_consent_by_user_id(user_id)
        if not consent or consent.is_revoked:
            raise AuthorizationError(
                "Debe otorgar consentimiento informado antes de participar en Mente Resiliente."
            )

        survey = WellbeingSurvey.create(
            user_id=user_id,
            neighborhood=command.neighborhood,
            mood_score=command.mood_score,
            raw_text=command.raw_text,
        )
        await self._repository.save_survey(survey)

        support_msg = None
        if survey.crisis_flag:
            # RF-18: Canalización inmediata de urgencias en Pereira
            support_msg = (
                "Hemos detectado señales de malestar emocional severo. "
                "No estás solo/a: puedes comunicarte gratuitamente en Pereira "
                "con la Línea de la Esperanza y Salud Mental marcando al 106 "
                "o al celular de urgencias 3228615710."
            )

        survey_id = survey.id.value
        return SurveyResult(
            survey_id=survey_id,
            crisis_detected=survey.crisis_flag,
            crisis_support_message=support_msg,
            neighborhood=survey.neighborhood,
            mood_score=survey.mood_score,
        )

    async def get_community_indicators(self) -> list[dict[str, Any]]:
        # RF-17: Indicadores agregados con umbral mínimo de 3 respuestas para k-anonimato
        return await self._repository.get_all_neighborhood_averages(min_samples=3)
