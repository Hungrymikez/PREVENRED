"""Esquemas HTTP del contexto operating_mode."""

from datetime import datetime

from pydantic import BaseModel, Field

from prevenred.operating_mode.domain.mode import OperationalModeType


class SwitchModeRequest(BaseModel):
    """Cuerpo de POST /mode/switch."""

    new_mode: OperationalModeType = Field(..., description="Nuevo estado: COTIDIANO o EMERGENCIA")
    reason: str = Field(..., min_length=10, description="Motivo formal del cambio de modo")


class OperationalModeResponse(BaseModel):
    """Representación pública del modo operacional vigente."""

    mode: OperationalModeType
    previous_mode: OperationalModeType
    changed_by: str
    reason: str
    created_at: datetime
    active: bool = True
