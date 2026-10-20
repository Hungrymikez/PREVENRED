"""
Eventos de dominio: hechos importantes que YA ocurrieron ("UsuarioRegistrado").

Sirven para que un contexto avise a otros sin acoplarse a ellos. Ejemplo:
cuando `identity` registra un Técnico, `services` podrá reaccionar creando
su perfil "Pendiente" (CU-01 paso 7) sin que identity conozca a services.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime


def utcnow() -> datetime:
    """Hora actual con zona UTC. Siempre usamos UTC dentro del sistema.

    Vive aquí (y no en `entity.py`) porque las entidades y los modelos de dominio
    la necesitan como `default_factory`: así importan un módulo sin dependencias
    y se evita el ciclo `events -> entity -> events`.
    """
    return datetime.now(UTC)


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base de los eventos de dominio: guarda cuándo ocurrió el hecho."""
    occurred_at: datetime = field(default_factory=utcnow)
