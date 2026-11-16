"""Pruebas del contexto incidents (CU-29, CU-39, RF-22..24)."""

from unittest.mock import MagicMock

import pytest

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role
from prevenred.auth.infrastructure.jwt_token_service import JwtTokenService
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

    def list_recent(self, status=None, limit=50, reported_by=None) -> list[Incident]:
        res = list(self.items.values())
        if status:
            res = [i for i in res if i.status == status]
        if reported_by is not None:
            res = [i for i in res if i.reported_by == reported_by]
        return res[:limit]

    def get_by_client_id(self, reported_by, client_id):
        return next(
            (
                i
                for i in self.items.values()
                if i.client_id == client_id and i.reported_by == reported_by
            ),
            None,
        )

    def get_by_case_number(self, case_number):
        return next((i for i in self.items.values() if i.case_number == case_number), None)


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
    incident.assigned_to = inspector.user_id  # el inspector solo gestiona sus casos asignados
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

    listed = client.get("/api/v1/incidents/", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert [i["id"] for i in listed.json()] == [data["id"]]


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
    # Sin asignación previa, quien gestiona el caso es el Administrador.
    inspector_jwt = tokens.issue(new_id(), Role.ADMINISTRADOR)

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


def _report(client, jwt: str, description: str) -> dict:
    response = client.post(
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {jwt}"},
        json={
            "incident_type": "INUNDACION",
            "severity": "MEDIA",
            "description": description,
            "longitude": -75.69,
            "latitude": 4.81,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_api_list_requires_auth(client) -> None:
    """Los reportes llevan datos personales: sin sesión no se listan."""
    assert client.get("/api/v1/incidents/").status_code == 401


def test_api_citizen_only_lists_own_incidents_and_staff_lists_all(client) -> None:
    tokens = JwtTokenService(get_settings())
    ana = tokens.issue(new_id(), Role.CIUDADANO)
    beto = tokens.issue(new_id(), Role.CIUDADANO)
    inspector = tokens.issue(new_id(), Role.INSPECTOR)
    admin = tokens.issue(new_id(), Role.ADMINISTRADOR)

    de_ana = _report(client, ana, "Agua entrando a la casa de Ana")
    de_beto = _report(client, beto, "Agua entrando a la casa de Beto")

    def ids(jwt: str) -> set[str]:
        response = client.get("/api/v1/incidents/", headers={"Authorization": f"Bearer {jwt}"})
        assert response.status_code == 200
        return {i["id"] for i in response.json()}

    assert ids(ana) == {de_ana["id"]}
    assert ids(beto) == {de_beto["id"]}
    assert ids(inspector) == ids(admin) == {de_ana["id"], de_beto["id"]}


def _body(**extra) -> dict:
    return {
        "incident_type": "VIVIENDA_DANADA",
        "severity": "MEDIA",
        "description": "Grietas en muros: la pared de la cocina se partió",
        "longitude": -75.69,
        "latitude": 4.81,
        **extra,
    }


def test_api_reintento_con_el_mismo_client_id_no_duplica(client) -> None:
    """CU-37 / H-07: el celular reintenta y el servidor devuelve el mismo caso."""
    jwt = JwtTokenService(get_settings()).issue(new_id(), Role.CIUDADANO)
    headers = {"Authorization": f"Bearer {jwt}"}
    body = _body(client_id="9b1f8c2e-celular-1", reported_at="2026-11-16T08:00:00Z")

    primero = client.post("/api/v1/incidents/", headers=headers, json=body)
    segundo = client.post("/api/v1/incidents/", headers=headers, json=body)

    assert primero.status_code == segundo.status_code == 201
    assert primero.json()["id"] == segundo.json()["id"]
    assert primero.json()["reported_at"].startswith("2026-11-16T08:00:00")
    listado = client.get("/api/v1/incidents/", headers=headers).json()
    assert len(listado) == 1


def test_api_consulta_por_numero_de_caso_respeta_al_dueno(client) -> None:
    tokens = JwtTokenService(get_settings())
    ana = {"Authorization": f"Bearer {tokens.issue(new_id(), Role.CIUDADANO)}"}
    beto = {"Authorization": f"Bearer {tokens.issue(new_id(), Role.CIUDADANO)}"}
    inspector = {"Authorization": f"Bearer {tokens.issue(new_id(), Role.INSPECTOR)}"}
    admin = {"Authorization": f"Bearer {tokens.issue(new_id(), Role.ADMINISTRADOR)}"}

    caso = client.post("/api/v1/incidents/", headers=ana, json=_body()).json()
    client.patch(
        f"/api/v1/incidents/{caso['id']}/status",
        headers=admin,
        json={"new_status": "EN_REVISION", "notes": "Revisando"},
    )
    url = f"/api/v1/incidents/case/{caso['case_number'].lower()}"

    propio = client.get(url, headers=ana)
    assert propio.status_code == 200
    assert propio.json()["status"] == "EN_REVISION"
    assert propio.json()["history"][0] == {
        "from_status": "REPORTADO",
        "to_status": "EN_REVISION",
        "changed_at": propio.json()["history"][0]["changed_at"],
        "notes": "Revisando",
    }
    # Otra persona no puede saber si el caso existe (E1).
    assert client.get(url, headers=beto).status_code == 404
    assert client.get(url, headers=inspector).status_code == 200


# ---------- CU-39: asignación de casos ----------


def _cuenta(db, make_user, rol: Role) -> tuple[str, dict]:
    """Crea una cuenta real en la base (para validar el rol al asignar) y su encabezado."""
    from prevenred.auth.infrastructure.mongo_user_repository import MongoUserRepository

    user = make_user(rol)
    MongoUserRepository(db).add(user)
    jwt = JwtTokenService(get_settings()).issue(user.id, rol)
    return user.id, {"Authorization": f"Bearer {jwt}"}


def test_admin_asigna_y_solo_el_inspector_asignado_gestiona(client, db, make_user) -> None:
    _, ciudadano = _cuenta(db, make_user, Role.CIUDADANO)
    _, admin = _cuenta(db, make_user, Role.ADMINISTRADOR)
    ana_id, ana = _cuenta(db, make_user, Role.INSPECTOR)
    _, beto = _cuenta(db, make_user, Role.INSPECTOR)
    caso = client.post("/api/v1/incidents/", headers=ciudadano, json=_body()).json()
    base = f"/api/v1/incidents/{caso['id']}"

    # Un inspector no puede asignar.
    assert (
        client.patch(f"{base}/assign", headers=ana, json={"assignee_id": ana_id}).status_code == 403
    )

    asignado = client.patch(
        f"{base}/assign", headers=admin, json={"assignee_id": ana_id, "notes": "Zona de Ana"}
    )
    assert asignado.status_code == 200
    assert asignado.json()["assigned_to"] == ana_id
    assert asignado.json()["status"] == "ASIGNADO"
    assert asignado.json()["history"][-1]["notes"] == "Zona de Ana"

    cambio = {"new_status": "EN_ATENCION", "notes": "En sitio"}
    assert client.patch(f"{base}/status", headers=beto, json=cambio).status_code == 403
    assert client.patch(f"{base}/status", headers=ana, json=cambio).status_code == 200

    mios = client.get("/api/v1/incidents/?assigned_to_me=true", headers=ana).json()
    assert [c["id"] for c in mios] == [caso["id"]]
    assert client.get("/api/v1/incidents/?assigned_to_me=true", headers=beto).json() == []


def test_solo_se_asigna_a_inspectores_activos(client, db, make_user) -> None:
    ciudadano_id, ciudadano = _cuenta(db, make_user, Role.CIUDADANO)
    _, admin = _cuenta(db, make_user, Role.ADMINISTRADOR)
    caso = client.post("/api/v1/incidents/", headers=ciudadano, json=_body()).json()
    url = f"/api/v1/incidents/{caso['id']}/assign"

    assert client.patch(url, headers=admin, json={"assignee_id": ciudadano_id}).status_code == 422
    assert client.patch(url, headers=admin, json={"assignee_id": new_id()}).status_code == 422


def test_listar_inspectores_solo_para_administrador(client, db, make_user) -> None:
    inspector_id, _ = _cuenta(db, make_user, Role.INSPECTOR)
    _, admin = _cuenta(db, make_user, Role.ADMINISTRADOR)
    _, ciudadano = _cuenta(db, make_user, Role.CIUDADANO)

    lista = client.get("/api/v1/auth/users?role=inspector", headers=admin)
    assert lista.status_code == 200
    assert [u["id"] for u in lista.json()] == [inspector_id]
    assert client.get("/api/v1/auth/users?role=inspector", headers=ciudadano).status_code == 403
