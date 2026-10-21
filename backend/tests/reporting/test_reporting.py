from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.main import app
from prevenred.shared.infrastructure.mongo import get_database


class MockAsyncCollection:
    def __init__(self, count: int = 0, docs: list[dict[str, Any]] | None = None) -> None:
        self._count = count
        self._docs = docs or []

    async def count_documents(self, filter: dict[str, Any]) -> int:
        return self._count

    def aggregate(self, pipeline: list[dict[str, Any]]):
        class AggCursor:
            def __init__(self, res: list[dict[str, Any]]) -> None:
                self._res = res

            async def to_list(self, length: int) -> list[dict[str, Any]]:
                return self._res

        return AggCursor([])

    def find(self, filter: dict[str, Any] | None = None):
        docs = self._docs

        class FindCursor:
            async def to_list(self, length: int) -> list[dict[str, Any]]:
                return docs

        return FindCursor()


class MockAsyncDatabase:
    def __init__(self, incident_docs: list[dict[str, Any]] | None = None) -> None:
        self._collections: dict[str, MockAsyncCollection] = {
            "incidents": MockAsyncCollection(count=5, docs=incident_docs or []),
            "property_inspections": MockAsyncCollection(count=2),
            "aid_needs": MockAsyncCollection(count=3),
            "aid_inventory": MockAsyncCollection(count=4),
            "donation_matches": MockAsyncCollection(count=1),
            "volunteers": MockAsyncCollection(count=10),
        }

    def __getitem__(self, name: str) -> MockAsyncCollection:
        if name not in self._collections:
            self._collections[name] = MockAsyncCollection()
        return self._collections[name]


@pytest.fixture
def admin_user() -> User:
    return User.register(
        email=Email("admin.reportes@pereira.gov.co"),
        raw_password="AdminPass2026*",
        name="Coordinador de Estadísticas",
        role=Role.ADMIN,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def citizen_user() -> User:
    return User.register(
        email=Email("vecino.reportes@pereira.gov.co"),
        raw_password="CitizenPass2026*",
        name="Vecino Comunero",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_dashboard_endpoint_structure() -> None:
    mock_db = MockAsyncDatabase()
    app.dependency_overrides[get_database] = lambda: mock_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/reporting/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert "total_incidents" in data
            assert "total_inspections" in data
            assert "active_volunteers" in data
            assert data["total_incidents"] == 5
            assert data["total_inspections"] == 2
            assert data["active_volunteers"] == 10
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_export_incidents_csv_as_admin(admin_user: User) -> None:
    mock_docs = [
        {
            "case_number": "INC-2026-001",
            "incident_type": "DESLIZAMIENTO",
            "severity": "ALTA",
            "status": "EN_ATENCION",
            "location": {"coordinates": [-75.69, 4.81]},
            "created_at": "2026-10-19T10:00:00Z",
        }
    ]
    mock_db = MockAsyncDatabase(incident_docs=mock_docs)
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/reporting/export/incidents/csv")
            assert response.status_code == 200
            data = response.json()
            assert "filename" in data
            assert data["filename"].startswith("prevenred_incidentes_")
            assert "INC-2026-001" in data["csv_content"]
            assert "DESLIZAMIENTO" in data["csv_content"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_export_incidents_csv_forbidden_for_citizen(citizen_user: User) -> None:
    mock_db = MockAsyncDatabase()
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: citizen_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/reporting/export/incidents/csv")
            assert response.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()
