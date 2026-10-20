"""Entidad OperationalMode: estado global Cotidiano/Emergencia (CU-04, RF-01)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.ids import EntityId, new_id


class OperationalModeType(StrEnum):
    """Modos operacionales globales (docs/db/operational_modes.md)."""

    COTIDIANO = "COTIDIANO"
    EMERGENCIA = "EMERGENCIA"


@dataclass(kw_only=True, eq=False)
class OperationalMode(Entity):
    """Registro de una transición de modo operacional (historial, RN-02)."""

    mode: OperationalModeType
    previous_mode: OperationalModeType
    changed_by: EntityId
    reason: str
    created_at: datetime
    active: bool = True
    ended_at: datetime | None = None
    mfa_verified: bool = False

    @classmethod
    def create(
        cls,
        *,
        new_mode: OperationalModeType,
        previous_mode: OperationalModeType,
        changed_by: EntityId,
        reason: str,
        mfa_verified: bool = False,
    ) -> "OperationalMode":
        """Crea una transición válida. Exige motivo (≥10) y modo distinto (CU-04 E4)."""
        cleaned_reason = reason.strip() if reason else ""
        if len(cleaned_reason) < 10:
            raise ValidationError("El motivo del cambio de modo debe tener al menos 10 caracteres.")
        if new_mode == previous_mode:
            raise ValidationError(f"El sistema ya se encuentra en modo {new_mode.value}.")

        return cls(
            id=new_id(),
            mode=new_mode,
            previous_mode=previous_mode,
            changed_by=changed_by,
            reason=cleaned_reason,
            created_at=utcnow(),
            active=True,
            ended_at=None,
            mfa_verified=mfa_verified,
        )

    @classmethod
    def default_cotidiano(cls) -> "OperationalMode":
        """Estado por defecto cuando aún no hay historial persistido."""
        return cls(
            id=new_id(),
            mode=OperationalModeType.COTIDIANO,
            previous_mode=OperationalModeType.COTIDIANO,
            changed_by="000000000000000000000000",
            reason="Inicialización por defecto del sistema.",
            created_at=utcnow(),
            active=True,
            ended_at=None,
            mfa_verified=False,
        )

    def close(self, ended_at: datetime | None = None) -> None:
        """Cierra este registro al activarse uno nuevo (conserva historial)."""
        self.active = False
        self.ended_at = ended_at or utcnow()
