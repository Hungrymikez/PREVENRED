"""Eventos que publica el contexto identity."""
from dataclasses import dataclass

from prevenred.shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class UserRegistered(DomainEvent):
    """Lo escuchará `services` para crear el perfil 'Pendiente' del técnico (CU-01 paso 7)."""
    user_id: str
    role: str
