from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_incidents: int
    incidents_by_status: dict[str, int]
    incidents_by_severity: dict[str, int]
    total_inspections: int
    inspections_by_habitability: dict[str, int]
    total_aid_needs: int
    total_aid_offers: int
    total_matches: int
    active_volunteers: int


class ExportCsvResponse(BaseModel):
    filename: str
    csv_content: str
