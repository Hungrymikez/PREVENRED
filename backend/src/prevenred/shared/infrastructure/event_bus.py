"""EventBus en memoria: suficiente para la v1.0 (un solo proceso)."""
from collections import defaultdict
from collections.abc import Callable

from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.events import DomainEvent


class InMemoryEventBus(EventBus):
    """Bus de eventos en memoria: suficiente mientras la API corra en un solo proceso."""
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[DomainEvent], None]) -> None:
        """Registra una función que se ejecutará cuando se publique un evento de ese tipo."""
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Ejecuta, en orden, los suscriptores del tipo de evento publicado."""
        for handler in self._handlers[type(event)]:
            handler(event)


# Instancia única del proceso (se inyecta con Depends en la capa interface).
event_bus = InMemoryEventBus()
