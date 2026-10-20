"""
Puertos de bienestar (CU-23, CU-24).

`SurveyRepository` no recibe NADA con lo que se pueda identificar a alguien: no
existe un "último envío de esta persona" ni nada equivalente. El límite semanal
vive en `ConsentRepository.record_survey_sent(user_id, purpose, week_key)`, que
sólo recibe la SEMANA; el repositorio de encuestas no tiene forma de vincular una
respuesta con una persona, ni siquiera por error de programación.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from prevenred.wellbeing.domain.entities import Consent, SurveyResponse


class ConsentRepository(ABC):
    """Puerto de los consentimientos informados (CU-24)."""

    @abstractmethod
    def get_by_id(self, consent_id: str) -> Consent | None:
        """Busca un consentimiento por id."""

    @abstractmethod
    def add(self, consent: Consent) -> None:
        """Registra una decisión de consentimiento."""

    @abstractmethod
    def update(self, consent: Consent) -> None:
        """Guarda la revocación."""

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Consent]:
        """Historial de la persona (más reciente primero)."""

    @abstractmethod
    def find_active(self, user_id: str, purpose: str) -> Consent | None:
        """Permiso vigente para una finalidad, o None."""

    @abstractmethod
    def record_survey_sent(self, user_id: str, purpose: str, week_key: str) -> None:
        """Marca que la persona ya envió su bienestar en esa semana ISO (O-08).

        Guarda sólo la semana (`2026-W41`) en el consentimiento vigente. Es el único
        punto del sistema que relaciona a una persona con un envío, y lo hace sin
        fecha ni hora ni id de la respuesta.
        """


class SurveyRepository(ABC):
    """Puerto de las respuestas anónimas de bienestar (CU-23)."""

    @abstractmethod
    def add(self, response: SurveyResponse) -> None:
        """Guarda una respuesta (sin datos identificatorios)."""

    @abstractmethod
    def count_between(self, start: datetime, end: datetime) -> int:
        """Cuántas respuestas hubo en el periodo (panel agregado, sin individuos)."""

