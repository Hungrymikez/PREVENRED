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


# ---- RN-05: `neighborhood` en la raíz y `location` como GeoJSON Point o null ----
def test_barrio_es_campo_raiz_y_location_nace_null(db):
    MongoUserRepository(db).add(_user())
    doc = db["users"].find_one({"email": "a@mail.com"})
    assert doc["neighborhood"] == "Dosquebradas"
    assert doc["location"] is None          # identity aún no captura coordenadas


def test_update_escribe_el_barrio_en_la_raiz(db):
    """El `$set` no puede volver a crear `location.neighborhood` (dato de GeoJSON)."""
    repo, user = MongoUserRepository(db), _user()
    repo.add(user)
    db["users"].update_one({"email": "a@mail.com"}, {"$set": {"neighborhood": "Cuba"}})
    loaded = repo.get_by_id(user.id)
    repo.update(loaded)
    doc = db["users"].find_one({"email": "a@mail.com"})
    assert doc["neighborhood"] == "Cuba"
    assert doc["location"] is None


def test_lee_documentos_viejos_con_location_neighborhood(db):
    """Un documento sin migrar (barrio dentro de location) se sigue leyendo."""
    repo, user = MongoUserRepository(db), _user()
    repo.add(user)
    db["users"].update_one(
        {"email": "a@mail.com"},
        {"$unset": {"neighborhood": ""}, "$set": {"location": {"neighborhood": "Centro"}}},
    )
    assert repo.get_by_id(user.id).neighborhood == "Centro"


def test_location_geojson_no_rompe_la_lectura_del_barrio(db):
    """`location` puede ser un Point real: el barrio sale del campo raíz."""
    repo, user = MongoUserRepository(db), _user()
    repo.add(user)
    db["users"].update_one(
        {"email": "a@mail.com"},
        {"$set": {"location": {"type": "Point", "coordinates": [-75.69, 4.81]}}},
    )
    loaded = repo.get_by_id(user.id)
    assert loaded.neighborhood == "Dosquebradas"

