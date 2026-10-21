"""Rutas HTTP del contexto operating_mode (CU-04, RF-01, RF-02)."""

from fastapi import APIRouter, Depends

from prevenred.auth.application.ports import TokenPayload
from prevenred.operating_mode.application.get_current_mode import GetCurrentOperationalMode
from prevenred.operating_mode.application.switch_mode import (
    SwitchModeCommand,
    SwitchOperationalMode,
)
from prevenred.operating_mode.interface.dependencies import (
    get_admin_token,
    get_current_operational_mode,
    get_switch_operational_mode,
)
from prevenred.operating_mode.interface.schemas import (
    OperationalModeResponse,
    SwitchModeRequest,
)

router = APIRouter(prefix="/api/v1/mode", tags=["Modo operacional (M02)"])


def _to_response(result) -> OperationalModeResponse:
    return OperationalModeResponse(
        mode=result.mode,
        previous_mode=result.previous_mode,
        changed_by=result.changed_by,
        reason=result.reason,
        created_at=result.created_at,
        active=result.active,
    )


@router.get(
    "/current",
    response_model=OperationalModeResponse,
    summary="Consultar modo operacional vigente (RF-02)",
)
def get_current_mode(
    use_case: GetCurrentOperationalMode = Depends(get_current_operational_mode),
) -> OperationalModeResponse:
    """Devuelve el modo Cotidiano/Emergencia vigente (sin autenticación)."""
    return _to_response(use_case.execute())


@router.post(
    "/switch",
    response_model=OperationalModeResponse,
    summary="CU-04 Cambiar modo operacional",
)
def switch_mode(
    body: SwitchModeRequest,
    use_case: SwitchOperationalMode = Depends(get_switch_operational_mode),
    operator: TokenPayload = Depends(get_admin_token),
) -> OperationalModeResponse:
    """Conmuta el modo global. Solo Administrador (RN-01)."""
    result = use_case.execute(
        SwitchModeCommand(
            new_mode=body.new_mode,
            reason=body.reason,
            operator=operator,
        )
    )
    return _to_response(result)
