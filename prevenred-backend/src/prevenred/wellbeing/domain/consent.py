"""Entidad de dominio para el consentimiento informado de bienestar."""

from dataclasses import dataclass
from datetime import UTC, datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


@dataclass
class WellbeingConsent(Entity):
    user_id: EntityId
    terms_version: str
    consented_at: datetime
    is_revoked: bool

    @classmethod
    def create(cls, user_id: EntityId, terms_version: str = "v1.0") -> "WellbeingConsent":
        if not terms_version or len(terms_version.strip()) == 0:
            raise DomainValidationError("Versión de términos requerida.")
        return cls(
            id=EntityId.generate(),
            user_id=user_id,
            terms_version=terms_version.strip(),
            consented_at=datetime.now(UTC),
            is_revoked=False,
        )
