"""Puerto EventBus: cómo se publican los eventos de dominio."""

from abc import ABC, abstractmethod

from prevenred.shared.domain.events import DomainEvent


class EventBus(ABC):
    """Puerto para publicar eventos de dominio sin conocer quién los escucha."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Entrega el evento a todos los suscriptores interesados."""
