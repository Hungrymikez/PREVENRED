"""Eventos que publica el contexto fieldwork."""

from dataclasses import dataclass

from prevenred.shared.domain.events import DomainEvent
from prevenred.shared.domain.ids import EntityId

from .inspection import DamageLevel, HabitabilityStatus


@dataclass(frozen=True, kw_only=True)
class InspectionSubmittedEvent(DomainEvent):
    """Publicado al registrar un censo/inspección (CU-36)."""

    inspection_id: EntityId
    inspector_id: EntityId
    damage_level: DamageLevel
    habitability: HabitabilityStatus
    neighborhood: str
