"""Pruebas del repositorio contra Mongo (mongomock): mapeo documento <-> entidad."""

import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.shared.domain.errors import ConflictError


def _user(email="a@mail.com") -> User:
    return User.register(
        full_name="Ana Gómez",
        email=Email(email),
        password_hash="h",
        role=Role.TECNICO_VOLUNTARIO,
        neighborhood="Dosquebradas",
        privacy_notice_version="v1",
        accepted_terms=True,
    )


def test_guardar_y_leer_conserva_los_datos(db):
    repo, user = MongoUserRepository(db), _user()
    repo.add(user)
    loaded = repo.get_by_id(user.id)
    assert loaded.email.value == "a@mail.com" and loaded.role is Role.TECNICO_VOLUNTARIO
    assert loaded.locked_until is None and loaded.is_active


def test_documento_sigue_el_diseno_del_doc_09(db):
    user = _user()
    MongoUserRepository(db).add(user)
    doc = db["users"].find_one({"email": "a@mail.com"})
    assert doc["roles"] == ["tecnico_voluntario"] and doc["status"] == "ACTIVE"
    assert doc["verified"] is False and "passwordHash" in doc


def test_indice_unico_de_correo(db):
    repo = MongoUserRepository(db)
    repo.add(_user())
    with pytest.raises(ConflictError):
        repo.add(_user())


def test_update_no_pisa_campos_de_otros_contextos(db):
    repo, user = MongoUserRepository(db), _user()
    repo.add(user)
    db["users"].update_one({"email": "a@mail.com"}, {"$set": {"verified": True}})
    user.register_failed_login(user.created_at)
    repo.update(user)
    assert db["users"].find_one({"email": "a@mail.com"})["verified"] is True


def test_to_entity_acepta_camel_case_y_snake_case(db):
    from datetime import UTC, datetime

    from bson import ObjectId

    from prevenred.identity.infrastructure.mongo_user_repository import _to_entity

    # Documento con formato snake_case y campos directos (estilo seed/scripts)
    doc_snake = {
        "_id": "000000000000000000000001",
        "email": "snake@mail.com",
        "full_name": "Usuario Snake",
        "password_hash": "hash_snake",
        "role": "ADMIN",
        "neighborhood": "Centro",
        "privacy_notice_version": "v1.0",
        "terms_accepted_at": datetime.now(UTC),
        "is_active": True,
        "failed_login_attempts": 0,
        "locked_until": None,
        "created_at": datetime.now(UTC),
    }
    user_from_snake = _to_entity(doc_snake)
    assert user_from_snake.full_name == "Usuario Snake"
    assert user_from_snake.password_hash == "hash_snake"
    assert user_from_snake.role is Role.ADMINISTRADOR
    assert user_from_snake.neighborhood == "Centro"
    assert user_from_snake.is_active is True

    # Documento con formato camelCase estándar (diseño doc 09)
    doc_camel = {
        "_id": ObjectId("000000000000000000000002"),
        "email": "camel@mail.com",
        "name": "Usuario Camel",
        "passwordHash": "hash_camel",
        "roles": ["inspector"],
        "status": "ACTIVE",
        "location": {"neighborhood": "Cuba"},
        "consent": {
            "privacyNoticeVersion": "v1.0",
            "acceptedAt": datetime.now(UTC),
        },
        "security": {
            "failedLoginAttempts": 2,
            "lockedUntil": None,
        },
        "createdAt": datetime.now(UTC),
    }
    user_from_camel = _to_entity(doc_camel)
    assert user_from_camel.full_name == "Usuario Camel"
    assert user_from_camel.password_hash == "hash_camel"
    assert user_from_camel.role is Role.INSPECTOR
    assert user_from_camel.neighborhood == "Cuba"
    assert user_from_camel.failed_login_attempts == 2
