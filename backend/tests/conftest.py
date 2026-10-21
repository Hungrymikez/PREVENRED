"""Fixtures compartidas: una API con MongoDB en memoria (mongomock) por cada test."""

import os
from pathlib import Path
from uuid import uuid4

import mongomock
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from pymongo import MongoClient

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.auth.infrastructure.indexes import ensure_indexes as identity_indexes
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.fieldwork.infrastructure.indexes import ensure_indexes as fieldwork_indexes
from prevenred.incidents.infrastructure.indexes import ensure_indexes as incidents_indexes
from prevenred.main import create_app
from prevenred.operating_mode.infrastructure.indexes import (
    ensure_indexes as operating_mode_indexes,
)
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.mongo import get_database, get_db
from tests.async_mongo import AsyncDatabase

# JWT_SECRET es obligatorio (la app no arranca sin él): valor fijo solo para pruebas.
os.environ.setdefault("JWT_SECRET", "prueba-local-no-usar-en-produccion-32bytes")
# Las pruebas validan el comportamiento de producción (MFA exigido), sin importar el .env local.
os.environ["ENVIRONMENT"] = "production"
os.environ["MFA_ENABLED"] = "true"
# Del .env solo se toma MONGO_TEST_URI (pruebas contra MongoDB real en una base temporal).
_test_uri = dotenv_values(Path(__file__).resolve().parents[1] / ".env").get("MONGO_TEST_URI")
if _test_uri:
    os.environ.setdefault("MONGO_TEST_URI", _test_uri)


def _safe_indexes(ensure, database) -> None:
    """mongomock no soporta bien 2dsphere; no fallar el fixture por eso."""
    try:
        ensure(database)
    except Exception:
        pass


@pytest.fixture
def db():
    database = mongomock.MongoClient()["pereira_responde_test"]
    identity_indexes(database)
    operating_mode_indexes(database)
    _safe_indexes(incidents_indexes, database)
    _safe_indexes(fieldwork_indexes, database)
    return database


@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)  # sin 'with': no ejecuta lifespan (no toca la BD real)


@pytest.fixture
def motor_db():
    """Base asíncrona (estilo Motor) en memoria para los contextos que usan Motor."""
    return AsyncDatabase(mongomock.MongoClient(tz_aware=True)["prevenred_async_test"])


@pytest.fixture
def api(db, motor_db):
    """API completa con ambas bases en memoria. Usa `act_as(user)` para fijar la sesión."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_database] = lambda: motor_db
    return TestClient(app)


@pytest.fixture
def make_user():
    """Crea una entidad User (sin hashing costoso) con el rol pedido."""

    def _make(role: Role = Role.CIUDADANO, name: str = "Usuario de Prueba") -> User:
        return User(
            full_name=name,
            email=Email(f"{uuid4().hex[:10]}@pereira.gov.co"),
            password_hash="hash-no-usable",
            role=role,
            neighborhood="Cuba",
            privacy_notice_version="v1",
            terms_accepted_at=utcnow(),
        )

    return _make


@pytest.fixture
def act_as(api):
    """Suplanta la sesión (get_current_user) del cliente `api` con el usuario dado."""

    def _act_as(user: User) -> User:
        api.app.dependency_overrides[get_current_user] = lambda: user
        return user

    return _act_as


@pytest.fixture
def real_db():
    """Base MongoDB REAL, solo si defines MONGO_TEST_URI (p. ej. mongodb://localhost:27017).
    Úsala para lo que mongomock no soporta bien: índices 2dsphere ($geoNear) y transacciones.
    Crea una base temporal y la borra al terminar."""
    uri = os.getenv("MONGO_TEST_URI")
    if not uri:
        pytest.skip("Define MONGO_TEST_URI para correr pruebas contra MongoDB real")
    client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=3000)
    name = f"prevenred_test_{uuid4().hex[:8]}"
    yield client[name]
    client.drop_database(name)
    client.close()
