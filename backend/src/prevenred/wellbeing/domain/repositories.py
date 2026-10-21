"""Interfaces de repositorios para el contexto de bienestar emocional."""

from abc import ABC, abstractmethod
from typing import Any

from prevenred.shared.domain.ids import EntityId

from .consent import WellbeingConsent
from .survey import WellbeingSurvey


class WellbeingRepository(ABC):
    @abstractmethod
    async def save_consent(self, consent: WellbeingConsent) -> None:
        pass

    @abstractmethod
    async def get_consent_by_user_id(self, user_id: EntityId) -> WellbeingConsent | None:
        pass

    @abstractmethod
    async def save_survey(self, survey: WellbeingSurvey) -> None:
        pass

    @abstractmethod
    async def get_all_neighborhood_averages(self, min_samples: int = 3) -> list[dict[str, Any]]:
        pass
