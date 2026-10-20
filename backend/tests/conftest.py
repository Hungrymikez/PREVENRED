"""Fixtures compartidas: una API con MongoDB en memoria (mongomock) por cada test."""
import os
from pathlib import Path
from uuid import uuid4

import mongomock
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pymongo import MongoClient

from prevenred.auth.infrastructure.indexes import ensure_indexes as identity_indexes
from prevenred.main import create_app
from prevenred.shared.infrastructure.mongo import get_db

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
os.environ.setdefault("JWT_SECRET", "prueba-local-no-usar-en-produccion-32bytes")


@pytest.fixture
def db():
    database = mongomock.MongoClient()["pereira_responde_test"]
    identity_indexes(database)   # los índices únicos también se prueban
    return database


@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)  # sin 'with': no ejecuta lifespan (no toca la BD real)


@pytest.fixture
def real_db():
    """Base MongoDB real (Atlas u otro) cuando MONGO_TEST_URI está definida.

    mongomock no cubre índices 2dsphere ni $nearSphere. Crea una base temporal
    y la borra al terminar; no toca la base prevenred de la aplicación.
    """
    uri = os.getenv("MONGO_TEST_URI")
    if not uri:
        pytest.skip("Define MONGO_TEST_URI para correr pruebas contra MongoDB real")
    client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=10000)
    name = f"prevenred_test_{uuid4().hex[:8]}"
    yield client[name]
    client.drop_database(name)
    client.close()
