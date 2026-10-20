"""
Entidad Notification: mensaje Push/SMS y su estado de entrega (CU-06, CU-07).

Por qué existe: el push puede fallar (sin datos, token vencido), y el sistema
debe reintentar y dejar rastro. También se guarda la lectura (`read_at`) para
CU-07. Los reintentos son finitos: repetir para siempre un número inválido
gastaría la cuota del proveedor y martillaría al destinatario.
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_one_of, require_text, require_utc

#: Canales disponibles (CU-06: Push y SMS).
CHANNELS = ("PUSH", "SMS")

#: Estados de entrega.
NOTIFICATION_STATUSES = ("PENDIENTE", "ENVIADO", "FALLIDO")

#: Tipos de aviso (CU-06). Se usa para agrupar y para el texto del ícono.
NOTIFICATION_TYPES = (
    "CRISIS",
    "ASIGNACION",
    "ESTADO_CASO",
    "AYUDA",
    "RECORDATORIO",
    "OTRO",
)

#: Reintentos máximos (política pendiente, O-16). Provisional.
MAX_ATTEMPTS = 3


@dataclass(kw_only=True, eq=False)
class Notification(Entity):
    """Aviso enviado a una persona por push o SMS."""
    user_id: str
    channel: str
    title: str
    message: str
    type: str = "OTRO"
    zone: str = ""                      # zona del aviso (para agregados)
    status: str = "PENDIENTE"
    attempts: int = 0
    sent_at: datetime | None = None
    last_error: str | None = None
    read_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida canal, texto y estado inicial."""
        require_text(self.user_id, "user_id", max_length=64)
        require_one_of(self.channel, CHANNELS, "channel")
        require_one_of(self.type, NOTIFICATION_TYPES, "type")
        require_one_of(self.status, NOTIFICATION_STATUSES, "status")
        require_text(self.title, "title", max_length=120)
        require_text(self.message, "message", max_length=500)
        if self.attempts < 0:
            raise ValidationError("Los intentos no pueden ser negativos.")
        if self.sent_at is not None:
            self.sent_at = require_utc(self.sent_at, "sent_at")
        if self.read_at is not None:
            self.read_at = require_utc(self.read_at, "read_at")

    def mark_sent(self, at: datetime) -> None:
        """El proveedor aceptó el mensaje (CU-06)."""
        self.status = "ENVIADO"
        self.sent_at = require_utc(at, "sent_at")
        self.last_error = None

    def mark_failed(self, error: str) -> bool:
        """Registra un intento fallido. True si todavía se puede reintentar.

        Se devuelve el booleano porque quien llama decide si programa el reintento;
        así la regla (límite de intentos) queda en el dominio y no en el router.
        """
        require_text(error, "error", max_length=500)
        self.attempts += 1
        self.last_error = error
        self.status = "FALLIDO"
        return self.can_retry

    @property
    def can_retry(self) -> bool:
        """True si aún quedan intentos y no se entregó."""
        return self.status != "ENVIADO" and self.attempts < MAX_ATTEMPTS

    def mark_read(self, at: datetime) -> None:
        """Marca la lectura en la campanita (CU-07). Idempotente: la primera gana."""
        if self.read_at is not None:
            return
        if self.status != "ENVIADO":
            raise ValidationError("No se puede marcar como leído un aviso sin enviar.")
        self.read_at = require_utc(at, "read_at")

    @property
    def is_read(self) -> bool:
        """True si la persona ya lo vio."""
        return self.read_at is not None
