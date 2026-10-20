"""Entidad y lógica de dominio para encuestas de bienestar emocional y triage de crisis."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId

CRISIS_PATTERNS = [
    r"\b(suicidi\w*|matarme|quitarme la vida|no quiero vivir|acabar con todo)\b",
    r"\b(autolesi\w*|cortarme|hacerme da[ñn]o)\b",
    r"\b(desesperaci[oó]n total|no puedo m[aá]s|no tengo salida)\b",
]


@dataclass
class WellbeingSurvey(Entity):
    user_id: EntityId
    neighborhood: str
    mood_score: int  # 1 (muy mal) a 5 (muy bien)
    sanitized_text: str
    crisis_flag: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: EntityId,
        neighborhood: str,
        mood_score: int,
        raw_text: str | None = None,
    ) -> "WellbeingSurvey":
        clean_neigh = neighborhood.strip() if neighborhood else ""
        if len(clean_neigh) < 2:
            raise DomainValidationError(
                "El nombre del barrio o comuna debe tener al menos 2 caracteres."
            )
        if not (1 <= mood_score <= 5):
            raise DomainValidationError("La escala de estado de ánimo debe estar entre 1 y 5.")

        text = raw_text.strip() if raw_text else ""
        # RNF-04: Sanitización de PII en capa de dominio
        sanitized = cls._sanitize_pii(text)
        is_crisis = cls._detect_crisis(text)

        return cls(
            id=EntityId.generate(),
            user_id=user_id,
            neighborhood=clean_neigh,
            mood_score=mood_score,
            sanitized_text=sanitized,
            crisis_flag=is_crisis,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _sanitize_pii(text: str) -> str:
        if not text:
            return ""
        # Enmascarar correos electrónicos
        sanitized = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[CORREO_PROTEGIDO]", text)
        # Enmascarar números de teléfono (+57 o 10 dígitos)
        sanitized = re.sub(
            r"(\+?57\s?)?3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}", "[TEL_PROTEGIDO]", sanitized
        )
        # Enmascarar posibles cédulas colombianas (6 a 10 dígitos continuos)
        sanitized = re.sub(r"\b\d{6,10}\b", "[ID_PROTEGIDO]", sanitized)
        return sanitized

    @staticmethod
    def _detect_crisis(text: str) -> bool:
        if not text:
            return False
        lower_text = text.lower()
        for pattern in CRISIS_PATTERNS:
            if re.search(pattern, lower_text):
                return True
        return False
