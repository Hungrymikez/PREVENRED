"""Pruebas del contexto incidents (CU-29, CU-39, RF-22..24)."""

from unittest.mock import MagicMock

import pytest

from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.domain.role import Role
from prevenred.identity.infrastructure.jwt_token_service import JwtTokenService
from prevenred.incidents.application.report_incident import (
    ReportIncident,
    ReportIncidentCommand,
)
from prevenred.incidents.application.update_incident_status import (
    UpdateIncidentStatus,
    UpdateIncidentStatusCommand,
)
from prevenred.incidents.domain.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from prevenred.incidents.domain.repositories import IncidentRepository
from prevenred.incidents.infrastructure.mongo_incident_repository import (
    MongoIncidentRepository,
)
from prevenred.shared.domain.errors import ForbiddenError, NotFoundError, ValidationError
from prevenred.shared.domain.ids import new_id
from prevenred.shared.infrastructure.config import get_settings


class InMemoryIncidentRepository(IncidentRepository):
    def __init__(self) -> None:
        self.items: dict[str, Incident] = {}

    def save(self, incident: Incident) -> None:
        self.items[incident.id] = incident

    def get_by_id(self, incident_id: str) -> Incident | None:
        return self.items.get(incident_id)

    def list_recent(self, status=None, limit=50) -> list[Incident]:
        res = list(self.items.values())
        if status:
            res = [i for i in res if i.status == status]
        return res[:limit]


def _citizen() -> TokenPayload:
    return TokenPayload(user_id=new_id(), role=Role.CIUDADANO)


def _inspector() -> TokenPayload:
    return TokenPayload(user_id=new_id(), role=Role.INSPECTOR)


def test_domain_rejects_short_description() -> None:
    with pytest.raises(ValidationError, match="al menos 5 caracteres"):
        Incident.create(
            incident_type=IncidentType.DESLIZAMIENTO,
            severity=IncidentSeverity.ALTA,
            description="x",
            longitude=-75.69,
            latitude=4.81,
            reported_by=new_id(),
        )


def test_domain_rejects_invalid_coordinates() -> None:
    with pytest.raises(ValidationError, match="Coordenadas"):
        Incident.create(
            incident_type=IncidentType.VIA_BLOQUEADA,
            severity=IncidentSeverity.MEDIA,
            description="Árbol caído bloquea la vía",
            longitude=-200.0,
            latitude=4.81,
            reported_by=new_id(),
        )


def test_report_incident_creates_valid_case_number() -> None:
    repo = InMemoryIncidentRepository()
    use_case = ReportIncident(repo, MagicMock())

    res = use_case.execute(
        ReportIncidentCommand(
            incident_type=IncidentType.DESLIZAMIENTO,
            severity=IncidentSeverity.ALTA,
            description="Deslizamiento en la ladera del barrio Boston",
            longitude=-75.69,
            latitude=4.81,
            reporter=_citizen(),
        )
    )

    assert res.id is not None
    assert res.case_number.startswith("INC-")
    assert res.status == IncidentStatus.REPORTED
    assert len(repo.items) == 1


def test_update_incident_status_permissions() -> None:
    repo = InMemoryIncidentRepository()
    citizen = _citizen()
    inspector = _inspector()
    incident = Incident.create(
        incident_type=IncidentType.VIA_BLOQUEADA,
        severity=IncidentSeverity.MEDIA,
        description="Arbol caido en la via circunvalar",
        longitude=-75.68,
        latitude=4.80,
        reported_by=citizen.user_id,
    )
    repo.save(incident)
    use_case = UpdateIncidentStatus(repo, MagicMock())

    with pytest.raises(ForbiddenError):
        use_case.execute(
            UpdateIncidentStatusCommand(
                incident_id=incident.id,
                new_status=IncidentStatus.IN_PROGRESS,
                notes="Intentando avanzar",
                operator=citizen,
            )
        )

    res = use_case.execute(
        UpdateIncidentStatusCommand(
            incident_id=incident.id,
            new_status=IncidentStatus.IN_PROGRESS,
            notes="Equipo de Bomberos en sitio",
            operator=inspector,
        )
    )
    assert res.status == IncidentStatus.IN_PROGRESS
    assert len(res.history) == 1


def test_update_incident_not_found() -> None:
    use_case = UpdateIncidentStatus(InMemoryIncidentRepository(), MagicMock())
    with pytest.raises(NotFoundError):
        use_case.execute(
            UpdateIncidentStatusCommand(
                incident_id=new_id(),
                new_status=IncidentStatus.IN_REVIEW,
                notes="No existe",
                operator=_inspector(),
            )
        )


def test_mongo_repository_roundtrip(db) -> None:
    repo = MongoIncidentRepository(db)
    incident = Incident.create(
        incident_type=IncidentType.INUNDACION,
        severity=IncidentSeverity.CRITICA,
        description="Inundacion en zona ribereña del Otun",
        longitude=-75.70,
        latitude=4.82,
        reported_by=new_id(),
        media_urls=["https://cdn.example/foto1.jpg"],
    )
    repo.save(incident)

    loaded = repo.get_by_id(incident.id)
    assert loaded is not None
    assert loaded.case_number == incident.case_number
    assert loaded.longitude == pytest.approx(-75.70)
    assert loaded.media_urls == ["https://cdn.example/foto1.jpg"]

    recent = repo.list_recent(status=IncidentStatus.REPORTED)
    assert len(recent) == 1


def test_api_report_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/incidents/",
        json={
            "incident_type": "DESLIZAMIENTO",
            "severity": "ALTA",
            "description": "Deslizamiento sin autenticacion",
            "longitude": -75.69,
            "latitude": 4.81,
        },
    )
    assert response.status_code == 401


def test_api_report_and_list_as_citizen(client) -> None:
    body = {
        "full_name": "Carlos Perez",
        "email": "carlos.incident@mail.com",
        "password": "clave-segura-1",
        "role": "ciudadano",
        "neighborhood": "Boston",
        "accepted_terms": True,
    }
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        json={"email": body["email"], "password": body["password"]},
    ).json()["access_token"]

    created = client.post(
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "incident_type": "DESLIZAMIENTO",
            "severity": "ALTA",
            "description": "Deslizamiento en la ladera del barrio Boston",
            "longitude": -75.69,
            "latitude": 4.81,
        },
    )
    assert created.status_code == 201
    data = created.json()
    assert data["case_number"].startswith("INC-")
    assert data["status"] == "REPORTADO"

    listed = client.get("/api/v1/incidents/")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_api_consecutive_incident_reports_generate_unique_case_numbers(client) -> None:
    tokens = JwtTokenService(get_settings())
    citizen_jwt = tokens.issue(new_id(), Role.CIUDADANO)

    res1 = client.post(
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {citizen_jwt}"},
        json={
            "incident_type": "DESLIZAMIENTO",
            "severity": "ALTA",
            "description": "Primer deslizamiento reportado",
            "longitude": -75.69,
            "latitude": 4.81,
        },
    )
    assert res1.status_code == 201
    data1 = res1.json()

    res2 = client.post(
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {citizen_jwt}"},
        json={
            "incident_type": "VIA_BLOQUEADA",
            "severity": "MEDIA",
            "description": "Segundo incidente: via tapada por escombros",
            "longitude": -75.70,
            "latitude": 4.82,
        },
    )
    assert res2.status_code == 201
    data2 = res2.json()

    assert data1["case_number"] != data2["case_number"]
    assert data1["case_number"].startswith("INC-")
    assert data2["case_number"].startswith("INC-")


def test_api_update_status_as_inspector(client) -> None:
    tokens = JwtTokenService(get_settings())
    citizen_id = new_id()
    citizen_jwt = tokens.issue(citizen_id, Role.CIUDADANO)
    inspector_jwt = tokens.issue(new_id(), Role.INSPECTOR)

    created = client.post(
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {citizen_jwt}"},
        json={
            "incident_type": "VIA_BLOQUEADA",
            "severity": "MEDIA",
            "description": "Arbol caido en la via circunvalar",
            "longitude": -75.68,
            "latitude": 4.80,
        },
    )
    incident_id = created.json()["id"]

    forbidden = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        headers={"Authorization": f"Bearer {citizen_jwt}"},
        json={"new_status": "EN_ATENCION", "notes": "sin permiso"},
    )
    assert forbidden.status_code == 403

    updated = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        headers={"Authorization": f"Bearer {inspector_jwt}"},
        json={"new_status": "EN_ATENCION", "notes": "Brigada en sitio"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "EN_ATENCION"
