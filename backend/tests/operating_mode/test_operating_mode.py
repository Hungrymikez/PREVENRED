"""Pruebas del contexto operating_mode (CU-04, RF-01, RF-02)."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role
from prevenred.auth.infrastructure.jwt_token_service import JwtTokenService
from prevenred.operating_mode.application.switch_mode import (
    SwitchModeCommand,
    SwitchOperationalMode,
)
from prevenred.operating_mode.domain.mode import OperationalMode, OperationalModeType
from prevenred.operating_mode.domain.repositories import OperationalModeRepository
from prevenred.operating_mode.infrastructure.mongo_mode_repository import (
    MongoOperationalModeRepository,
)
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.ids import new_id
from prevenred.shared.infrastructure.config import get_settings


class MockModeRepository(OperationalModeRepository):
    def __init__(self, initial_mode: OperationalModeType = OperationalModeType.COTIDIANO) -> None:
        self.records: list[OperationalMode] = [
            OperationalMode(
                id=new_id(),
                mode=initial_mode,
                previous_mode=initial_mode,
                changed_by="000000000000000000000000",
                reason="Initial system state",
                created_at=utcnow(),
            )
        ]

    def get_current_mode(self) -> OperationalMode:
        return self.records[-1]

    def save(self, mode_record: OperationalMode) -> None:
        for previous in self.records:
            if previous.active:
                previous.close(mode_record.created_at)
        self.records.append(mode_record)


def _admin_token() -> TokenPayload:
    return TokenPayload(user_id=new_id(), role=Role.ADMINISTRADOR)


def _citizen_token() -> TokenPayload:
    return TokenPayload(user_id=new_id(), role=Role.CIUDADANO)


def test_domain_mode_creation_validation() -> None:
    with pytest.raises(ValidationError, match="al menos 10 caracteres"):
        OperationalMode.create(
            new_mode=OperationalModeType.EMERGENCIA,
            previous_mode=OperationalModeType.COTIDIANO,
            changed_by=new_id(),
            reason="Corta",
        )

    with pytest.raises(ValidationError, match="ya se encuentra en modo"):
        OperationalMode.create(
            new_mode=OperationalModeType.COTIDIANO,
            previous_mode=OperationalModeType.COTIDIANO,
            changed_by=new_id(),
            reason="Motivo valido de conmutacion",
        )


def test_switch_mode_use_case_success() -> None:
    repo = MockModeRepository()
    mock_bus = MagicMock()
    use_case = SwitchOperationalMode(repo, mock_bus)

    result = use_case.execute(
        SwitchModeCommand(
            new_mode=OperationalModeType.EMERGENCIA,
            reason="Declaratoria de emergencia por deslizamiento en ladera Rio Otun",
            operator=_admin_token(),
        )
    )

    assert result.mode == OperationalModeType.EMERGENCIA
    assert result.previous_mode == OperationalModeType.COTIDIANO
    mock_bus.publish.assert_called_once()
    assert repo.get_current_mode().mode == OperationalModeType.EMERGENCIA


def test_switch_mode_forbidden_for_non_admin() -> None:
    repo = MockModeRepository()
    use_case = SwitchOperationalMode(repo, MagicMock())

    with pytest.raises(ForbiddenError):
        use_case.execute(
            SwitchModeCommand(
                new_mode=OperationalModeType.EMERGENCIA,
                reason="Intento no autorizado de activar emergencia",
                operator=_citizen_token(),
            )
        )


def test_mongo_repository_default_and_persist(db) -> None:
    repo = MongoOperationalModeRepository(db)
    current = repo.get_current_mode()
    assert current.mode == OperationalModeType.COTIDIANO

    record = OperationalMode.create(
        new_mode=OperationalModeType.EMERGENCIA,
        previous_mode=OperationalModeType.COTIDIANO,
        changed_by=new_id(),
        reason="Activacion de emergencia por inundacion en zona ribereña",
    )
    repo.save(record)

    current = repo.get_current_mode()
    assert current.mode == OperationalModeType.EMERGENCIA
    assert current.reason.startswith("Activacion")
    assert current.active is True

    # Historial: el documento anterior queda cerrado, no se borra.
    docs = list(db["operational_modes"].find())
    assert len(docs) == 1  # solo se persistió el cambio (default no se guardó)


def test_api_get_current_mode_endpoint(client) -> None:
    response = client.get("/api/v1/mode/current")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] in ["COTIDIANO", "EMERGENCIA"]
    assert "reason" in data
    assert "created_at" in data


def test_api_switch_mode_unauthorized_without_jwt(client) -> None:
    response = client.post(
        "/api/v1/mode/switch",
        json={
            "new_mode": "EMERGENCIA",
            "reason": "Activacion sin token de autenticacion",
        },
    )
    assert response.status_code in (401, 403)


def test_api_switch_mode_forbidden_for_citizen(client) -> None:
    # Ciudadano vía registro + login.
    body = {
        "full_name": "Carlos Perez",
        "email": "carlos.mode@mail.com",
        "password": "clave-segura-1",
        "role": "ciudadano",
        "neighborhood": "Cuba",
        "accepted_terms": True,
    }
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": body["email"], "password": body["password"]},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/mode/switch",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "new_mode": "EMERGENCIA",
            "reason": "Intento de ciudadano de activar emergencia",
        },
    )
    assert response.status_code == 403


def test_api_switch_mode_success_as_admin(client) -> None:
    tokens = JwtTokenService(get_settings())
    admin_id = new_id()
    jwt = tokens.issue(admin_id, Role.ADMINISTRADOR)

    response = client.post(
        "/api/v1/mode/switch",
        headers={"Authorization": f"Bearer {jwt}"},
        json={
            "new_mode": "EMERGENCIA",
            "reason": "Declaratoria formal de emergencia municipal por sismo",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "EMERGENCIA"
    assert data["previous_mode"] == "COTIDIANO"
    assert data["changed_by"] == admin_id

    current = client.get("/api/v1/mode/current")
    assert current.json()["mode"] == "EMERGENCIA"
    assert isinstance(
        datetime.fromisoformat(current.json()["created_at"].replace("Z", "+00:00")), datetime
    )
