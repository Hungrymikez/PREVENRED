"""Puerto de persistencia de notificaciones (CU-06, CU-07)."""
from abc import ABC, abstractmethod

from prevenred.notifications.domain.notification import Notification


class NotificationRepository(ABC):
    """Puerto de los avisos push/SMS y su estado de entrega."""

    @abstractmethod
    def get_by_id(self, notification_id: str) -> Notification | None:
        """Busca un aviso por id."""

    @abstractmethod
    def add(self, notification: Notification) -> None:
        """Guarda un aviso pendiente de envío."""

    @abstractmethod
    def add_many(self, notifications: list[Notification]) -> None:
        """Guarda un lote (p. ej. aviso de crisis a toda una zona)."""

    @abstractmethod
    def update(self, notification: Notification) -> None:
        """Guarda el estado de entrega, los intentos o la lectura."""

    @abstractmethod
    def list_by_user(
        self, user_id: str, *, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        """Avisos de una persona, del más reciente al más antiguo (CU-07)."""

    @abstractmethod
    def list_pending(self, *, limit: int = 200) -> list[Notification]:
        """Avisos que aún no llegaron a 'ENVIADO' (reintentos del servicio)."""
