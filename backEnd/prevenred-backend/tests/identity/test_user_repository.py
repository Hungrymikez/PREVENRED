"""Pruebas del repositorio contra Mongo (mongomock): mapeo documento <-> entidad."""
import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.shared.domain.errors import ConflictError


def _user(email="a@mail.com") -> User:
    return User.register(
        full_name="Ana Gómez", email=Email(email), password_hash="h", roles=(Role.TECNICO,),
        neighborhood="Dosquebradas", privacy_notice_version="v1", accepted_terms=True,
    )


def test_guardar_y_leer_conserva_los_datos(db):
    repo, user = MongoUserRepository(db), _user()
    repo.add(user)
    loaded = repo.get_by_id(user.id)
    assert loaded.email.value == "a@mail.com" and loaded.role is Role.TECNICO
    assert loaded.locked_until is None and loaded.is_active


def test_documento_sigue_el_diseno_del_doc_09(db):
    user = _user()
    MongoUserRepository(db).add(user)
    doc = db["users"].find_one({"email": "a@mail.com"})
    assert doc["roles"] == ["TECNICO"] and doc["status"] == "ACTIVE"
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
