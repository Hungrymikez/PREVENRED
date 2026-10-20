"""Caja blanca de la infraestructura compartida y del composition root (main.py)."""

from datetime import UTC, datetime, timedelta, timezone

import mongomock
import pytest
from fastapi.testclient import TestClient

import prevenred.main as main_module
from prevenred.shared.domain import errors as e
from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.events import DomainEvent
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure import config, mongo
from prevenred.shared.infrastructure.event_bus import InMemoryEventBus
from tests.async_mongo import AsyncDatabase

# ---------- Traductor de errores de dominio -> HTTP ----------


@pytest.mark.parametrize(
    ("error_cls", "status", "code"),
    [
        (e.DomainError, 400, "domain_error"),  # rama por defecto del mapa
        (e.ValidationError, 422, "validation_error"),
        (e.UnauthorizedError, 401, "unauthorized"),
        (e.ForbiddenError, 403, "forbidden"),
        (e.NotFoundError, 404, "not_found"),
        (e.ConflictError, 409, "conflict"),
        (e.TooManyAttemptsError, 429, "too_many_attempts"),
    ],
)
def test_cada_error_de_dominio_tiene_su_codigo_http(error_cls, status, code):
    app = main_module.create_app()

    @app.get("/_boom")
    def boom():
        raise error_cls("mensaje de prueba")

    r = TestClient(app).get("/_boom")
    assert r.status_code == status
    assert r.json() == {"error": {"code": code, "message": "mensaje de prueba"}}


def test_aliases_de_errores_apuntan_a_las_clases_canonicas():
    assert e.DomainValidationError is e.ValidationError
    assert e.AuthorizationError is e.ForbiddenError


# ---------- Bus de eventos en memoria ----------


class _EventoA(DomainEvent):
    pass


class _EventoB(DomainEvent):
    pass


def test_bus_entrega_en_orden_y_solo_al_tipo_suscrito():
    bus, received = InMemoryEventBus(), []
    bus.subscribe(_EventoA, lambda ev: received.append(("primero", ev)))
    bus.subscribe(_EventoA, lambda ev: received.append(("segundo", ev)))
    bus.subscribe(_EventoB, lambda ev: received.append(("otro", ev)))

    evento = _EventoA()
    bus.publish(evento)
    assert received == [("primero", evento), ("segundo", evento)]


def test_publicar_sin_suscriptores_no_falla():
    InMemoryEventBus().publish(_EventoA())


# ---------- Entity: identidad ----------


class _Cosa(Entity):
    pass


class _OtraCosa(Entity):
    pass


def test_entity_normaliza_id_str_a_entityid():
    cosa = _Cosa(id="64b7f0c2a1b2c3d4e5f60718")
    assert isinstance(cosa.id, EntityId)


def test_igualdad_por_identidad_y_tipo():
    a, b = _Cosa(id="x1"), _Cosa(id="x1")
    assert a == b and hash(a) == hash(b)
    assert a != _Cosa(id="x2")
    assert a != _OtraCosa(id="x1")  # mismo id, distinto tipo
    assert a != "x1"
    assert len({a, b}) == 1


def test_pull_events_vacia_la_cola():
    cosa = _Cosa()
    cosa.record_event(_EventoA())
    assert len(cosa.pull_events()) == 1
    assert cosa.pull_events() == []


# ---------- Configuración y conexión ----------


@pytest.fixture
def fresh_settings(monkeypatch):
    for var in ("MONGO_URI", "MONGODB_URI", "MONGO_DB_NAME", "MONGODB_DB_NAME"):
        monkeypatch.delenv(var, raising=False)
    caches = (config.get_settings, mongo.get_client, mongo.get_motor_client)
    for cached in caches:
        cached.cache_clear()
    yield monkeypatch
    for cached in caches:
        cached.cache_clear()


def test_settings_aceptan_nombres_alternativos_de_variables(fresh_settings):
    fresh_settings.setenv("MONGODB_URI", "mongodb://otro-host:27017")
    fresh_settings.setenv("MONGODB_DB_NAME", "prevenred_alt")
    s = config.Settings(_env_file=None)
    assert (s.mongo_uri, s.mongo_db_name) == ("mongodb://otro-host:27017", "prevenred_alt")


def test_clientes_mongo_se_crean_una_vez_y_apuntan_a_la_base_configurada(fresh_settings):
    fresh_settings.setenv("MONGO_URI", "mongodb://127.0.0.1:1")  # conexión perezosa
    fresh_settings.setenv("MONGO_DB_NAME", "prevenred_unit")

    assert mongo.get_db().name == "prevenred_unit"
    assert mongo.get_client() is mongo.get_client()
    assert mongo.get_database().name == "prevenred_unit"
    assert mongo.get_motor_client() is mongo.get_motor_client()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (datetime(2026, 1, 1, 12), datetime(2026, 1, 1, 12, tzinfo=UTC)),
        (
            datetime(2026, 1, 1, 12, tzinfo=timezone(timedelta(hours=-5))),
            datetime(2026, 1, 1, 17, tzinfo=UTC),
        ),
    ],
)
def test_as_utc(value, expected):
    assert mongo.as_utc(value) == expected


# ---------- Arranque (lifespan) y suscriptores ----------


def test_lifespan_crea_indices_sincronos_y_asincronos(monkeypatch):
    sync_db = mongomock.MongoClient()["boot_sync"]
    async_db = AsyncDatabase(mongomock.MongoClient()["boot_async"])
    monkeypatch.setattr(main_module, "get_db", lambda: sync_db)
    monkeypatch.setattr(main_module, "get_database", lambda: async_db)

    with TestClient(main_module.create_app()):
        pass

    assert "email" in str(sync_db["users"].index_information())
    for collection in ("aid_inventory", "aid_needs", "materials", "technicians", "volunteers"):
        assert "location_2dsphere" in async_db[collection].index_information(), collection
    assert async_db["technicians"].index_information()["user_id_1"]["unique"] is True
    assert "created_at_1" in async_db["audit_logs"].index_information()
    assert "neighborhood_1" in async_db["wellbeing_surveys"].index_information()


def test_create_app_registra_los_suscriptores_de_eventos(monkeypatch):
    calls = []
    monkeypatch.setattr(main_module, "EVENT_SUBSCRIBERS", [calls.append])
    main_module.create_app()
    assert calls == [main_module.event_bus]
