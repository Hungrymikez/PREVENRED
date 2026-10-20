"""
Entity: objeto con identidad propia (dos usuarios con el mismo nombre
siguen siendo distintos porque tienen distinto id).

Todas las entidades del proyecto son dataclasses (`@dataclass(kw_only=True, eq=False)`)
y heredan de `Entity`: así el dominio queda limpio y sin librerías técnicas.
Los modelos Pydantic SOLO viven en `interface/schemas.py` (entrada/salida HTTP).
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.events import DomainEvent, utcnow
from prevenred.shared.domain.ids import EntityId, new_id


class _EventBuffer:
    """Contenedor de eventos propios de UNA instancia (no se declara como atributo)."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []


class EntityBase:
    """Comportamiento común de toda entidad: anotar y entregar eventos de dominio."""
    id: EntityId
    created_at: datetime

    def record_event(self, event: DomainEvent) -> None:
        """Anota un evento que se publicará después de guardar en la base de datos."""
        self._events.events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Entrega y limpia los eventos pendientes de ESTA instancia."""
        events = self._events.events
        object.__setattr__(self, "_buffer", _EventBuffer())
        return events

    @property
    def _events(self) -> _EventBuffer:
        """Buffer de eventos creado al primer uso (no se comparte entre instancias)."""
        if "_buffer" not in self.__dict__:
            object.__setattr__(self, "_buffer", _EventBuffer())
        return self.__dict__["_buffer"]


@dataclass(kw_only=True, eq=False)
class Entity(EntityBase):
    """Base de las entidades de dominio (dataclass).

    `eq=False` + igualdad por id: dos `User` con los mismos datos son el MISMO
    usuario; dos `Incident` con el mismo texto siguen siendo distintos.
    """
    id: EntityId = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utcnow)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EntityBase) and type(self) is type(other) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
