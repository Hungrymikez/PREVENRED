"""Cableado del contexto operating_mode (inyección de dependencias)."""

from fastapi import Depends
from pymongo.database import Database

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role
from prevenred.auth.interface.dependencies import require_roles
from prevenred.operating_mode.application.get_current_mode import GetCurrentOperationalMode
from prevenred.operating_mode.application.switch_mode import SwitchOperationalMode
from prevenred.operating_mode.domain.repositories import OperationalModeRepository
from prevenred.operating_mode.infrastructure.mongo_mode_repository import (
    MongoOperationalModeRepository,
)
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_db


def get_mode_repository(db: Database = Depends(get_db)) -> OperationalModeRepository:
    """Entrega el repositorio de modos operacionales."""
    return MongoOperationalModeRepository(db)


def get_event_bus() -> EventBus:
    """Entrega el bus de eventos compartido."""
    return event_bus


def get_current_operational_mode(
    repo: OperationalModeRepository = Depends(get_mode_repository),
) -> GetCurrentOperationalMode:
    """Arma el caso de uso de consulta del modo vigente."""
    return GetCurrentOperationalMode(repo)


def get_switch_operational_mode(
    repo: OperationalModeRepository = Depends(get_mode_repository),
    events: EventBus = Depends(get_event_bus),
) -> SwitchOperationalMode:
    """Arma el caso de uso CU-04."""
    return SwitchOperationalMode(repo, events)


# Dependencia RBAC: solo Administrador puede conmutar (RN-01).
require_admin = require_roles(Role.ADMINISTRADOR)


def get_admin_token(
    token: TokenPayload = Depends(require_admin),
) -> TokenPayload:
    """Exige sesión de administrador; reutiliza require_roles de identity."""
    return token
