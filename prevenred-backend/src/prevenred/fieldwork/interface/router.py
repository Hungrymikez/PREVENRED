"""Rutas HTTP del contexto fieldwork (CU-34, CU-36; RF-19..21)."""

from fastapi import APIRouter, Depends

from prevenred.fieldwork.application.submit_inspection import (
    SubmitInspection,
    SubmitInspectionCommand,
)
from prevenred.fieldwork.domain.inspection import PropertyInspection
from prevenred.fieldwork.interface.dependencies import get_field_token, get_submit_inspection
from prevenred.fieldwork.interface.schemas import (
    PropertyInspectionResponse,
    SubmitInspectionRequest,
)
from prevenred.identity.application.ports import TokenPayload

router = APIRouter(prefix="/api/v1/fieldwork", tags=["Campo e inspecciones (M10)"])


def _to_response(inspection: PropertyInspection) -> PropertyInspectionResponse:
    return PropertyInspectionResponse(
        id=inspection.id,
        property_address=inspection.property_address,
        neighborhood=inspection.neighborhood,
        residents_count=inspection.residents_count,
        damage_level=inspection.damage_level,
        habitability=inspection.habitability,
        technical_notes=inspection.technical_notes,
        longitude=inspection.longitude,
        latitude=inspection.latitude,
        inspector_id=inspection.inspector_id,
        photos=inspection.photos,
        created_at=inspection.created_at,
    )


@router.post(
    "/inspections",
    response_model=PropertyInspectionResponse,
    status_code=201,
    summary="CU-36 Registrar inspección",
)
def submit_inspection(
    body: SubmitInspectionRequest,
    use_case: SubmitInspection = Depends(get_submit_inspection),
    inspector: TokenPayload = Depends(get_field_token),
) -> PropertyInspectionResponse:
    """Registra un censo/inspección de habitabilidad (inspector o admin)."""
    result = use_case.execute(
        SubmitInspectionCommand(
            property_address=body.property_address,
            neighborhood=body.neighborhood,
            residents_count=body.residents_count,
            damage_level=body.damage_level,
            habitability=body.habitability,
            technical_notes=body.technical_notes,
            longitude=body.longitude,
            latitude=body.latitude,
            inspector=inspector,
            photos=body.photos,
        )
    )
    return _to_response(result)
