"""Caja blanca del mapeo Mongo de usuarios (documentos legacy) y del RBAC por rol."""

import pytest
from bson import ObjectId

from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.mongo_user_repository import (
    MongoUserRepository,
    _parse_role,
    _to_entity,
)
from prevenred.identity.interface.dependencies import require_roles
from prevenred.shared.domain.errors import ForbiddenError
from prevenred.shared.domain.events import utcnow


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (Role.INSPECTOR, Role.INSPECTOR),  # ya es Role
        (["administrador", "ciudadano"], Role.ADMINISTRADOR),  # lista: toma el primero
        ("  Inspector ", Role.INSPECTOR),  # por valor, sin importar mayúsculas
        ("ADMIN", Role.ADMINISTRADOR),  # por nombre de alias
        ("rol-desconocido", Role.CIUDADANO),  # ni valor ni nombre -> por defecto
        (None, Role.CIUDADANO),
        ([], Role.CIUDADANO),
    ],
)
def test_parse_role_cubre_todas_las_formas(raw, expected):
    assert _parse_role(raw) is expected


@pytest.mark.parametrize(
    ("doc_fields", "expected_active"),
    [
        ({"is_active": False}, False),
        ({"isActive": False}, False),
        ({"status": "SUSPENDED"}, False),
        ({"status": "ACTIVE"}, True),
        ({}, True),
    ],
)
def test_estado_activo_acepta_formatos_legacy(doc_fields, expected_active):
    doc = {"_id": "u-1", "email": "a@b.co", "name": "Ana Gómez", **doc_fields}
    assert _to_entity(doc).is_active is expected_active


def _legacy_user() -> User:
    return User(
        id="usuario-legacy-01",  # id que NO es ObjectId (datos migrados)
        full_name="Ana Gómez",
        email=Email("legacy@mail.com"),
        password_hash="h",
        role=Role.CIUDADANO,
        neighborhood="Cuba",
        privacy_notice_version="v1",
        terms_accepted_at=utcnow(),
    )


def test_repositorio_soporta_ids_que_no_son_objectid(db):
    user = _legacy_user()
    db["users"].insert_one({"_id": user.id, "email": user.email.value, "name": user.full_name})
    repo = MongoUserRepository(db)

    loaded = repo.get_by_id(user.id)
    assert loaded is not None and loaded.id == user.id

    user.full_name = "Ana María Gómez"
    repo.update(user)
    assert db["users"].find_one({"_id": user.id})["name"] == "Ana María Gómez"


def test_get_by_id_con_objectid_guardado_como_string(db):
    oid = str(ObjectId())
    db["users"].insert_one({"_id": oid, "email": "s@mail.com", "name": "Ana Gómez"})
    assert MongoUserRepository(db).get_by_id(oid).email.value == "s@mail.com"


def test_require_roles_permite_y_rechaza():
    checker = require_roles(Role.INSPECTOR, Role.ADMINISTRADOR)
    allowed = TokenPayload(user_id="u", role=Role.INSPECTOR)
    assert checker(token=allowed) is allowed
    with pytest.raises(ForbiddenError):
        checker(token=TokenPayload(user_id="u", role=Role.CIUDADANO))
