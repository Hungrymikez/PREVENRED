"""Eventos que publica el contexto operating_mode."""

from dataclasses import dataclass

from prevenred.shared.domain.events import DomainEvent
from prevenred.shared.domain.ids import EntityId

from .mode import OperationalModeType


@dataclass(frozen=True, kw_only=True)
class OperationalModeChangedEvent(DomainEvent):
    """Publicado tras conmutar el modo (CU-04 paso 9; lo escucharán notificaciones/auditoría)."""

    mode: OperationalModeType
    previous_mode: OperationalModeType
    changed_by: EntityId
    reason: str
