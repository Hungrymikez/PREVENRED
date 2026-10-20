"""Pruebas del contexto fieldwork (CU-34, CU-36; RF-19..21)."""

from unittest.mock import MagicMock

import pytest

from prevenred.fieldwork.application.submit_inspection import (
    SubmitInspection,
    SubmitInspectionCommand,
)
from prevenred.fieldwork.domain.inspection import (
    DamageLevel,
    HabitabilityStatus,
    PropertyInspection,
)
from prevenred.fieldwork.domain.repositories import FieldworkRepository
from prevenred.fieldwork.infrastructure.mongo_fieldwork_repository import (
    MongoFieldworkRepository,
)
from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.domain.role import Role
from prevenred.identity.infrastructure.jwt_token_service import JwtTokenService
from prevenred.shared.domain.errors import ForbiddenError, ValidationError
from prevenred.shared.domain.ids import new_id
from prevenred.shared.infrastructure.config import get_settings


class InMemoryFieldworkRepository(FieldworkRepository):
    def __init__(self) -> None:
        self.items: dict[str, PropertyInspection] = {}

    def save(self, inspection: PropertyInspection) -> None:
        self.items[inspection.id] = inspection

    def get_by_id(self, inspection_id: str) -> PropertyInspection | None:
        return self.items.get(inspection_id)

    def list_by_inspector(self, inspector_id: str) -> list[PropertyInspection]:
        return [i for i in self.items.values() if i.inspector_id == inspector_id]


def _inspector() -> TokenPayload:
    return TokenPayload(user_id=new_id(), role=Role.INSPECTOR)


def _citizen() -> TokenPayload:
    return TokenPayload(user_id=new_id(), role=Role.CIUDADANO)


def test_domain_rejects_short_address() -> None:
    with pytest.raises(ValidationError, match="dirección"):
        PropertyInspection.create(
            property_address="x",
            neighborhood="Centro",
            residents_count=1,
            damage_level=DamageLevel.LEVE,
            habitability=HabitabilityStatus.HABITABLE,
            technical_notes="ok",
            longitude=-75.69,
            latitude=4.81,
            inspector_id=new_id(),
        )


def test_domain_rejects_negative_residents() -> None:
    with pytest.raises(ValidationError, match="residentes"):
        PropertyInspection.create(
            property_address="Carrera 7 # 18-20",
            neighborhood="Centro",
            residents_count=-1,
            damage_level=DamageLevel.LEVE,
            habitability=HabitabilityStatus.HABITABLE,
            technical_notes="ok",
            longitude=-75.69,
            latitude=4.81,
            inspector_id=new_id(),
        )


def test_submit_inspection_by_inspector() -> None:
    repo = InMemoryFieldworkRepository()
    use_case = SubmitInspection(repo, MagicMock())
    inspector = _inspector()

    res = use_case.execute(
        SubmitInspectionCommand(
            property_address="Carrera 7 # 18-20",
            neighborhood="Centro",
            residents_count=4,
            damage_level=DamageLevel.SEVERO,
            habitability=HabitabilityStatus.EVACUACION,
            technical_notes="Falla estructural en muro de carga posterior",
            longitude=-75.69,
            latitude=4.81,
            inspector=inspector,
            photos=["https://s3.amazonaws.com/evidence/1.jpg"],
        )
    )

    assert res.id is not None
    assert res.habitability == HabitabilityStatus.EVACUACION
    assert res.damage_level == DamageLevel.SEVERO
    assert len(repo.items) == 1
    assert repo.list_by_inspector(inspector.user_id)[0].id == res.id


def test_submit_inspection_forbidden_for_citizen() -> None:
    use_case = SubmitInspection(InMemoryFieldworkRepository(), MagicMock())

    with pytest.raises(ForbiddenError):
        use_case.execute(
            SubmitInspectionCommand(
                property_address="Calle 20 # 5-10",
                neighborhood="San Judas",
                residents_count=2,
                damage_level=DamageLevel.LEVE,
                habitability=HabitabilityStatus.HABITABLE,
                technical_notes="Solo fisuras en revoque",
                longitude=-75.70,
                latitude=4.82,
                inspector=_citizen(),
            )
        )


def test_mongo_repository_roundtrip(db) -> None:
    repo = MongoFieldworkRepository(db)
    inspection = PropertyInspection.create(
        property_address="Calle 14 # 9-30",
        neighborhood="Cuba",
        residents_count=3,
        damage_level=DamageLevel.MODERADO,
        habitability=HabitabilityStatus.RESTRINGIDO,
        technical_notes="Grietas diagonales en fachada",
        longitude=-75.71,
        latitude=4.79,
        inspector_id=new_id(),
    )
    repo.save(inspection)

    loaded = repo.get_by_id(inspection.id)
    assert loaded is not None
    assert loaded.neighborhood == "Cuba"
    assert loaded.damage_level == DamageLevel.MODERADO
    assert loaded.longitude == pytest.approx(-75.71)

    by_inspector = repo.list_by_inspector(inspection.inspector_id)
    assert len(by_inspector) == 1


def test_api_submit_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/fieldwork/inspections",
        json={
            "property_address": "Carrera 7 # 18-20",
            "neighborhood": "Centro",
            "residents_count": 2,
            "damage_level": "LEVE",
            "habitability": "HABITABLE",
            "technical_notes": "Sin daño estructural",
            "longitude": -75.69,
            "latitude": 4.81,
        },
    )
    assert response.status_code in (401, 403)


def test_api_submit_forbidden_for_citizen(client) -> None:
    body = {
        "full_name": "Vecino Local",
        "email": "vecino.field@mail.com",
        "password": "clave-segura-1",
        "role": "ciudadano",
        "neighborhood": "Centro",
        "accepted_terms": True,
    }
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        json={"email": body["email"], "password": body["password"]},
    ).json()["access_token"]

    response = client.post(
        "/api/v1/fieldwork/inspections",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_address": "Calle 20 # 5-10",
            "neighborhood": "San Judas",
            "residents_count": 2,
            "damage_level": "LEVE",
            "habitability": "HABITABLE",
            "technical_notes": "Solo fisuras en revoque",
            "longitude": -75.70,
            "latitude": 4.82,
        },
    )
    assert response.status_code == 403


def test_api_submit_as_inspector(client) -> None:
    tokens = JwtTokenService(get_settings())
    jwt = tokens.issue(new_id(), Role.INSPECTOR)

    response = client.post(
        "/api/v1/fieldwork/inspections",
        headers={"Authorization": f"Bearer {jwt}"},
        json={
            "property_address": "Carrera 7 # 18-20",
            "neighborhood": "Centro",
            "residents_count": 4,
            "damage_level": "SEVERO",
            "habitability": "EVACUACION",
            "technical_notes": "Falla estructural en muro de carga posterior",
            "longitude": -75.69,
            "latitude": 4.81,
            "photos": ["https://cdn.example/ev1.jpg"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["habitability"] == "EVACUACION"
    assert data["damage_level"] == "SEVERO"
    assert data["neighborhood"] == "Centro"
