"""
Entidades de bienestar: `Consent` y `SurveyResponse`.

Punto crítico de privacidad (CU-23, RN-03, O-07/O-08): la encuesta **no guarda
nada que identifique a la persona**. Ni `userId`, ni `respondentId`, ni ningún
hash de la cuenta (el "seudónimo" que se usaba antes quedó eliminado): sólo las
respuestas, la zona, la fecha y un `triggerEventId` opcional. El límite de una
respuesta por semana no se lleva en la encuesta, sino en el consentimiento, que
sí es por usuario y va en su propia colección: allí se guarda
`lastSurveyWeekKey` (`2026-W41`), **sólo la semana, nunca la hora**, así que el
consentimiento no dice a qué hora respondió nadie. Aceptar el aviso de
privacidad tampoco puede quedar dentro del documento anónimo.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import (
    require_between,
    require_one_of,
    require_text,
    require_utc,
)

#: Finalidades de consentimiento (CU-24).
CONSENT_PURPOSES = ("ANALITICA_BIENESTAR", "NOTIFICACIONES", "UBICACION_PRECISA")

#: Forma de la clave semanal (`2026-W41`): año ISO y semana de dos dígitos.
_WEEK_KEY_RE = re.compile(r"^\d{4}-W\d{2}$")


@dataclass(kw_only=True, eq=False)
class Consent(Entity):
    """Aceptación o revocación del aviso de privacidad (CU-24).

    Separado de `SurveyResponse` a propósito: mientras existe un consentimiento
    vigente sí se puede atribuir la decisión a la cuenta; las respuestas siguen
    siendo anónimas.
    """
    user_id: str
    purpose: str
    privacy_notice_version: str
    granted: bool = True
    granted_at: datetime = field(default_factory=utcnow)
    revoked_at: datetime | None = None
    #: Semana ISO del último envío de bienestar (`2026-W41`). Sólo la SEMANA, nunca
    #: la hora: es lo único que el consentimiento sabe de las respuestas (O-08).
    last_survey_week_key: str | None = None

    def __post_init__(self) -> None:
        """Valida la finalidad, la versión aceptada y las fechas."""
        require_text(self.user_id, "user_id", max_length=64)
        require_one_of(self.purpose, CONSENT_PURPOSES, "purpose")
        require_text(self.privacy_notice_version, "privacy_notice_version", max_length=20)
        self.granted_at = require_utc(self.granted_at, "granted_at")
        if self.last_survey_week_key is not None:
            require_text(self.last_survey_week_key, "last_survey_week_key", max_length=10)
            if not _WEEK_KEY_RE.match(self.last_survey_week_key):
                raise ValidationError(
                    "last_survey_week_key debe tener la forma AAAA-Wss (por ejemplo 2026-W41)."
                )
        if self.revoked_at is not None:
            self.revoked_at = require_utc(self.revoked_at, "revoked_at")
            if self.revoked_at < self.granted_at:
                raise ValidationError("La revocación no puede ser anterior al consentimiento.")
            self.granted = False

    @property
    def active(self) -> bool:
        """True si el permiso sigue concedido."""
        return self.granted and self.revoked_at is None

    def revoke(self, at: datetime | None = None) -> None:
        """Retira el permiso; debe detener de inmediato el tratamiento (CU-24)."""
        if not self.active:
            raise ValidationError("Este consentimiento ya fue retirado.")
        self.granted = False
        self.revoked_at = require_utc(at or utcnow(), "revoked_at")

    def record_survey_sent(self, at: datetime | None = None) -> None:
        """Anota la semana del envío de bienestar para limitarlo a una por semana (O-08).

        Guarda `week_key(at)` y **nada más**: la hora del envío no se conserva ni
        aquí ni en la encuesta, así que no hay forma de casar una respuesta con
        una persona por su marca de tiempo.
        """
        self.last_survey_week_key = week_key(at or utcnow())


def week_key(moment: datetime) -> str:
    """Clave ISO de la semana (`2026-W41`) usada para el límite de 1 por semana."""
    year, week, _ = require_utc(moment, "moment").isocalendar()
    return f"{year}-W{week:02d}"


@dataclass(kw_only=True, eq=False)
class SurveyResponse(Entity):
    """Respuesta ANÓNIMA al pulso de bienestar (CU-23).

    Anónima por construcción: no tiene `respondent_id`, ni `user_id`, ni ningún
    hash de la cuenta (RN-03). El `created_at` es la única fecha, y no se cruza
    con el consentimiento: el barrido semanal usa `Consent.last_survey_week_key`.
    """

    answers: dict
    zone: str | None = None
    trigger_event_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida la escala 1-5 y la fecha."""
        if not self.answers:
            raise ValidationError("La encuesta no tiene respuestas.")
        for key, value in self.answers.items():
            require_text(key, "answers.key", max_length=60)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(f"La respuesta '{key}' debe ser numérica.")
            require_between(value, 1, 5, key)
        if self.zone is not None:
            require_text(self.zone, "zone", max_length=80)
        self.created_at = require_utc(self.created_at, "created_at")

    @property
    def week_key(self) -> str:
        """Semana a la que pertenece la respuesta (se guarda en el consentimiento)."""
        return week_key(self.created_at)

    def was_sent_in(self, last_week_key: str | None) -> bool:
        """True si ya hay un envío de la persona en esta misma semana ISO.

        Recibe **sólo la semana** que trae el consentimiento (`2026-W41`), nunca una
        fecha ni un id: la encuesta no tiene manera de consultar quién respondió.
        """
        return last_week_key is not None and last_week_key == self.week_key

