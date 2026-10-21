"""Caja blanca de lo integrado desde main: PrevenRED2, MFA configurable, JWT_SECRET y nearby."""

import mongomock
import pytest
from pydantic import ValidationError as SettingsError
from pymongo.errors import OperationFailure

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.auth.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.geo.infrastructure.nearby import find_layers_near
from prevenred.incidents.infrastructure.nearby import find_incidents_near
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.infrastructure import mongo
from prevenred.shared.infrastructure.config import Settings

SECRET = "x" * 40


# ---------- User.register: coordenadas opcionales ----------


def _register(**overrides) -> User:
    data = {
        "full_name": "Mariana López",
        "email": Email("m@mail.com"),
        "password_hash": "h",
        "role": Role.TECNICO_VOLUNTARIO,
        "neighborhood": "Cuba",
        **overrides,
    }
    return User.register(**data)


@pytest.mark.parametrize(
    "coords",
    [
        {"latitude": 4.8},  # falta longitud
        {"longitude": -75.7},  # falta latitud
        {"latitude": 90.0001, "longitude": 0.0},
        {"latitude": 0.0, "longitude": -180.0001},
    ],
)
def test_register_valida_coordenadas(coords):
    with pytest.raises(ValidationError):
        _register(**coords)


def test_register_acepta_limites_y_limpia_habilidades():
    user = _register(
        latitude=-90.0, longitude=180.0, phone=" 3155559876 ", volunteer_skills=[" Rescate ", " "]
    )
    assert (user.latitude, user.longitude, user.phone) == (-90.0, 180.0, "3155559876")
    assert user.volunteer_skills == ["Rescate"]
    assert user.has_volunteer_profile is True


# ---------- Documento PrevenRED2 ----------


def test_documento_incluye_ubicacion_y_perfil_tecnico(db):
    user = _register(latitude=4.81, longitude=-75.69, role=Role.CIUDADANO)
    MongoUserRepository(db).add(user)
    doc = db["users"].find_one()
    assert doc["roles"] == ["CIUDADANO"]
    assert doc["location"] == {"type": "Point", "coordinates": [-75.69, 4.81]}
    assert doc["perfil_voluntario"] is None


def test_cuenta_tecnica_existente_conserva_codigo_y_perfil_tecnico(db):
    user = _register(role=Role.CIUDADANO)
    user.role_code = "TECNICO"
    user.technical_profile = {"oficio": "PLOMERIA"}
    MongoUserRepository(db).add(user)
    doc = db["users"].find_one()
    assert doc["roles"] == ["TECNICO"]  # no se reescribe el código ya existente
    assert doc["perfil_tecnico"] == {"oficio": "PLOMERIA"}
    assert doc["perfil_voluntario"] is None


# ---------- Configuración: JWT_SECRET obligatorio y MFA ----------


@pytest.mark.parametrize("secret", ["corto", "cambia-esto-" + "x" * 30, "secret" * 8, " " * 40])
def test_jwt_secret_inseguro_impide_arrancar(secret):
    with pytest.raises(SettingsError):
        Settings(_env_file=None, jwt_secret=secret)


@pytest.mark.parametrize(
    ("environment", "mfa_enabled", "requires"),
    [
        ("production", True, True),
        ("development", True, False),
        (" Development ", True, False),
        ("production", False, False),
    ],
)
def test_mfa_de_administrador_segun_entorno(environment, mfa_enabled, requires):
    s = Settings(
        _env_file=None, jwt_secret=SECRET, environment=environment, mfa_enabled=mfa_enabled
    )
    assert s.admin_login_requires_mfa is requires


# ---------- ensure_index: idempotente y tolerante a Atlas ----------


def test_ensure_index_no_duplica_un_indice_equivalente():
    col = mongomock.MongoClient()["db"]["users"]
    col.create_index("email", unique=True)  # nombre por defecto: email_1
    mongo.ensure_index(col, "email", name="uq_users_email", unique=True)
    assert "uq_users_email" not in col.index_information()


class _FailingCollection:
    def __init__(self, code: int) -> None:
        self.code = code

    def index_information(self):
        return {"_id_": {"key": [("_id", 1)]}}

    def create_index(self, *args, **kwargs):
        raise OperationFailure("conflicto", code=self.code)


def test_ensure_index_ignora_conflicto_de_nombre_85():
    mongo.ensure_index(_FailingCollection(85), "email", name="uq")


def test_ensure_index_propaga_otros_errores():
    with pytest.raises(OperationFailure):
        mongo.ensure_index(_FailingCollection(11000), [("email", 1)], name="uq")


# ---------- Consultas nearby: forma de la consulta $nearSphere ----------


class _RecordingDb:
    def __init__(self) -> None:
        self.queries: list[tuple[str, dict]] = []

    def __getitem__(self, name):
        db = self

        class _Col:
            def find(self, query):
                db.queries.append((name, query))
                return iter([{"_id": 1}])

        return _Col()


@pytest.mark.parametrize(
    ("finder", "collection", "field"),
    [(find_incidents_near, "incidents", "location"), (find_layers_near, "map_layers", "geometry")],
)
def test_nearby_construye_near_sphere(finder, collection, field):
    db = _RecordingDb()
    assert finder(db, -75.69, 4.81, 2000) == [{"_id": 1}]
    [(name, query)] = db.queries
    assert name == collection
    assert query[field]["$nearSphere"] == {
        "$geometry": {"type": "Point", "coordinates": [-75.69, 4.81]},
        "$maxDistance": 2000,
    }


def test_ciudadano_sin_codigo_de_rol_no_lleva_perfiles():
    from prevenred.auth.infrastructure.mongo_user_repository import _to_document

    doc = _to_document(_register(role=Role.CIUDADANO))
    assert (doc["perfil_tecnico"], doc["perfil_voluntario"]) == (None, None)
