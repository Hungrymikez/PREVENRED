"""Rutas HTTP del contexto incidents (CU-29, CU-39, RF-22..24)."""

from fastapi import APIRouter, Depends, Query

from prevenred.auth.application.ports import TokenPayload
from prevenred.incidents.application.assign_incident import (
    AssignIncident,
    AssignIncidentCommand,
)
from prevenred.incidents.application.list_incidents import (
    GetIncidentByCaseNumber,
    ListIncidents,
)
from prevenred.incidents.application.report_incident import (
    ReportIncident,
    ReportIncidentCommand,
)
from prevenred.incidents.application.update_incident_status import (
    UpdateIncidentStatus,
    UpdateIncidentStatusCommand,
)
from prevenred.incidents.domain.incident import Incident, IncidentStatus
from prevenred.incidents.interface.dependencies import (
    get_assign_incident,
    get_incident_by_case_number,
    get_list_incidents,
    get_report_incident,
    get_staff_token,
    get_update_incident_status,
    get_user_role_lookup,
    require_authenticated,
)
from prevenred.incidents.interface.schemas import (
    AssignIncidentRequest,
    IncidentHistoryEntry,
    IncidentResponse,
    ReportIncidentRequest,
    UpdateIncidentStatusRequest,
)

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidentes (M09)"])


def _to_response(incident: Incident) -> IncidentResponse:
    return IncidentResponse(
        id=incident.id,
        case_number=incident.case_number,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        longitude=incident.longitude,
        latitude=incident.latitude,
        reported_by=incident.reported_by,
        media_urls=incident.media_urls,
        created_at=incident.created_at,
        reported_at=incident.reported_at or incident.created_at,
        assigned_to=incident.assigned_to,
        history=[
            IncidentHistoryEntry(
                from_status=h.previous_status,
                to_status=h.new_status,
                changed_at=h.changed_at,
                notes=h.notes,
            )
            for h in incident.history
        ],
    )


@router.post("/", response_model=IncidentResponse, status_code=201, summary="CU-29 Reportar")
def report_incident(
    body: ReportIncidentRequest,
    use_case: ReportIncident = Depends(get_report_incident),
    reporter: TokenPayload = Depends(require_authenticated),
) -> IncidentResponse:
    """Crea un reporte georreferenciado de emergencia."""
    result = use_case.execute(
        ReportIncidentCommand(
            incident_type=body.incident_type,
            severity=body.severity,
            description=body.description,
            longitude=body.longitude,
            latitude=body.latitude,
            reporter=reporter,
            media_urls=body.media_urls,
            client_id=body.client_id,
            reported_at=body.reported_at,
        )
    )
    return _to_response(result)


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse,
    summary="CU-39 Actualizar estado",
)
def update_incident_status(
    incident_id: str,
    body: UpdateIncidentStatusRequest,
    use_case: UpdateIncidentStatus = Depends(get_update_incident_status),
    operator: TokenPayload = Depends(get_staff_token),
) -> IncidentResponse:
    """Cambia el estado del incidente (admin o inspector)."""
    result = use_case.execute(
        UpdateIncidentStatusCommand(
            incident_id=incident_id,
            new_status=body.new_status,
            notes=body.notes,
            operator=operator,
        )
    )
    return _to_response(result)


@router.get("/", response_model=list[IncidentResponse], summary="Listar incidentes")
def list_incidents(
    use_case: ListIncidents = Depends(get_list_incidents),
    requester: TokenPayload = Depends(require_authenticated),
    incident_status: IncidentStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    assigned_to_me: bool = Query(False, description="Solo los asignados a mí (personal)"),
) -> list[IncidentResponse]:
    """Lista reportes recientes (filtro opcional por estado).

    Exige sesión. Administrador e inspector ven todos; los demás roles, solo los suyos.
    """
    items = use_case.execute(
        requester=requester,
        status=incident_status,
        limit=limit,
        assigned_to_me=assigned_to_me,
    )
    return [_to_response(i) for i in items]


@router.get(
    "/case/{case_number}",
    response_model=IncidentResponse,
    summary="CU-32 Consultar un caso por número",
)
def get_incident_by_case_number_route(
    case_number: str,
    use_case: GetIncidentByCaseNumber = Depends(get_incident_by_case_number),
    requester: TokenPayload = Depends(require_authenticated),
) -> IncidentResponse:
    """Devuelve el caso con su historial. El ciudadano solo ve los suyos (404 si no)."""
    return _to_response(use_case.execute(requester, case_number))


@router.patch(
    "/{incident_id}/assign",
    response_model=IncidentResponse,
    summary="CU-39 Asignar a un inspector",
)
def assign_incident(
    incident_id: str,
    body: AssignIncidentRequest,
    use_case: AssignIncident = Depends(get_assign_incident),
    role_of=Depends(get_user_role_lookup),
    operator: TokenPayload = Depends(get_staff_token),
) -> IncidentResponse:
    """Asigna el caso a un inspector activo. Solo Administrador."""
    result = use_case.execute(
        AssignIncidentCommand(
            incident_id=incident_id,
            assignee_id=body.assignee_id,
            assignee_role=role_of(body.assignee_id),
            notes=body.notes,
            operator=operator,
        )
    )
    return _to_response(result)
