"""
Entity: objeto con identidad propia (dos usuarios con el mismo nombre
siguen siendo distintos porque tienen distinto id).
"""

from dataclasses import dataclass, field

from prevenred.shared.domain.events import DomainEvent
from prevenred.shared.domain.ids import EntityId, new_id


@dataclass(kw_only=True, eq=False)
class Entity:
    """Base de las entidades de dominio: identidad propia y eventos pendientes de publicar."""

    id: EntityId = field(default_factory=new_id)
    # Eventos pendientes de publicar; se publican DESPUÉS de guardar en BD.
    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.id, EntityId):
            self.id = EntityId(str(self.id))

    def record_event(self, event: DomainEvent) -> None:
        """Anota un evento que se publicará después de guardar en la base de datos."""
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Entrega y limpia los eventos pendientes."""
        events, self._events = self._events, []
        return events

    # Igualdad por identidad, no por atributos.
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entity) and type(self) is type(other) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
