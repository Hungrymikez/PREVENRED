"""CU-36 · Registrar inspección de habitabilidad."""

from dataclasses import dataclass

from prevenred.auth.application.ports import TokenPayload
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ForbiddenError

from ..domain.events import InspectionSubmittedEvent
from ..domain.inspection import DamageLevel, HabitabilityStatus, PropertyInspection
from ..domain.repositories import FieldworkRepository

_FIELD_ROLES = frozenset({"inspector", "administrador"})


@dataclass(frozen=True)
class SubmitInspectionCommand:
    """Datos de entrada de la inspección (sin detalles HTTP)."""

    property_address: str
    neighborhood: str
    residents_count: int
    damage_level: DamageLevel
    habitability: HabitabilityStatus
    technical_notes: str
    longitude: float
    latitude: float
    inspector: TokenPayload
    photos: list[str] | None = None


class SubmitInspection:
    """Caso de uso CU-36: solo evaluadores de campo o admin registran censos."""

    def __init__(self, repository: FieldworkRepository, event_bus: EventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    def execute(self, command: SubmitInspectionCommand) -> PropertyInspection:
        if command.inspector.role.value not in _FIELD_ROLES:
            raise ForbiddenError(
                "Solo evaluadores de campo autorizados o administradores pueden registrar censos."
            )

        inspection = PropertyInspection.create(
            property_address=command.property_address,
            neighborhood=command.neighborhood,
            residents_count=command.residents_count,
            damage_level=command.damage_level,
            habitability=command.habitability,
            technical_notes=command.technical_notes,
            longitude=command.longitude,
            latitude=command.latitude,
            inspector_id=command.inspector.user_id,
            photos=command.photos,
        )
        self._repository.save(inspection)
        self._event_bus.publish(
            InspectionSubmittedEvent(
                inspection_id=inspection.id,
                inspector_id=inspection.inspector_id,
                damage_level=inspection.damage_level,
                habitability=inspection.habitability,
                neighborhood=inspection.neighborhood,
                occurred_at=inspection.created_at,
            )
        )
        return inspection
