import csv
import io
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.shared.domain.errors import AuthorizationError
from prevenred.shared.infrastructure.mongo import get_database

from .schemas import DashboardSummaryResponse, ExportCsvResponse

router = APIRouter(prefix="/reporting", tags=["Reporting & Official Dashboards"])


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> DashboardSummaryResponse:
    # 1. Indicadores de Incidentes
    incidents_col = db["incidents"]
    total_inc = await incidents_col.count_documents({})
    inc_status_agg = await incidents_col.aggregate(
        [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    ).to_list(10)
    inc_status = {r["_id"]: r["count"] for r in inc_status_agg if r.get("_id") is not None}

    inc_sev_agg = await incidents_col.aggregate(
        [{"$group": {"_id": "$severity", "count": {"$sum": 1}}}]
    ).to_list(10)
    inc_sev = {r["_id"]: r["count"] for r in inc_sev_agg if r.get("_id") is not None}

    # 2. Indicadores de Censo de Inmuebles
    inspections_col = db["property_inspections"]
    total_insp = await inspections_col.count_documents({})
    insp_hab_agg = await inspections_col.aggregate(
        [{"$group": {"_id": "$habitability", "count": {"$sum": 1}}}]
    ).to_list(10)
    insp_hab = {r["_id"]: r["count"] for r in insp_hab_agg if r.get("_id") is not None}

    # 3. Ayudas y Voluntariado
    total_needs = await db["aid_needs"].count_documents({})
    total_offers = await db["aid_inventory"].count_documents({})
    total_matches = await db["donation_matches"].count_documents({})
    volunteers = await db["volunteers"].count_documents({"is_available": True})

    return DashboardSummaryResponse(
        total_incidents=total_inc,
        incidents_by_status=inc_status,
        incidents_by_severity=inc_sev,
        total_inspections=total_insp,
        inspections_by_habitability=insp_hab,
        total_aid_needs=total_needs,
        total_aid_offers=total_offers,
        total_matches=total_matches,
        active_volunteers=volunteers,
    )


@router.get("/export/incidents/csv", response_model=ExportCsvResponse)
async def export_incidents_csv(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> ExportCsvResponse:
    if current_user.role != Role.ADMIN:
        raise AuthorizationError("Solo administradores pueden exportar datos oficiales.")

    docs = await db["incidents"].find().to_list(1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["case_number", "type", "severity", "status", "longitude", "latitude", "created_at"]
    )

    for doc in docs:
        coords = doc.get("location", {}).get("coordinates", [0.0, 0.0])
        writer.writerow(
            [
                doc.get("case_number", ""),
                doc.get("incident_type", ""),
                doc.get("severity", ""),
                doc.get("status", ""),
                coords[0],
                coords[1],
                doc.get("created_at", ""),
            ]
        )

    now_str = datetime.now(UTC).strftime("%Y%m%d_%H%M")
    return ExportCsvResponse(
        filename=f"prevenred_incidentes_{now_str}.csv",
        csv_content=output.getvalue(),
    )
