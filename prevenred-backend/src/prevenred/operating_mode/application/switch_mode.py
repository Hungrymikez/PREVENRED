"""CU-04 · Cambiar modo operacional."""

from dataclasses import dataclass

from prevenred.identity.application.ports import TokenPayload
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ForbiddenError

from ..domain.events import OperationalModeChangedEvent
from ..domain.mode import OperationalMode, OperationalModeType
from ..domain.repositories import OperationalModeRepository


@dataclass(frozen=True)
class SwitchModeCommand:
    """Datos de entrada del caso de uso (sin detalles HTTP)."""

    new_mode: OperationalModeType
    reason: str
    operator: TokenPayload
    mfa_verified: bool = False


class SwitchOperationalMode:
    """Caso de uso CU-04: conmuta Cotidiano ↔ Emergencia (RN-01, RN-02)."""

    def __init__(
        self,
        repository: OperationalModeRepository,
        event_bus: EventBus,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus

    def execute(self, command: SwitchModeCommand) -> OperationalMode:
        # RN-01 / E1: solo administradores autorizados.
        if not command.operator.role.is_administrative:
            raise ForbiddenError(
                "Solo administradores autorizados pueden conmutar el modo operacional."
            )

        current = self._repository.get_current_mode()

        new_record = OperationalMode.create(
            new_mode=command.new_mode,
            previous_mode=current.mode,
            changed_by=command.operator.user_id,
            reason=command.reason,
            mfa_verified=command.mfa_verified,
        )

        self._repository.save(new_record)

        self._event_bus.publish(
            OperationalModeChangedEvent(
                mode=new_record.mode,
                previous_mode=new_record.previous_mode,
                changed_by=new_record.changed_by,
                reason=new_record.reason,
                occurred_at=new_record.created_at,
            )
        )
        return new_record
