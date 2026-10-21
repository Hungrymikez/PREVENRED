"""Caja blanca de incidentes y habitabilidad: ramas de dominio, mapeo Mongo e índices."""

import mongomock
import pytest
from bson import ObjectId

from prevenred.fieldwork.domain.inspection import (
    DamageLevel,
    HabitabilityStatus,
    PropertyInspection,
)
from prevenred.incidents.domain.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from prevenred.incidents.infrastructure.indexes import ensure_indexes
from prevenred.incidents.infrastructure.mongo_incident_repository import (
    COLLECTION,
    MongoIncidentRepository,
)
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.ids import new_id


def _incident(**overrides) -> Incident:
    data = {
        "incident_type": IncidentType.DESLIZAMIENTO,
        "severity": IncidentSeverity.ALTA,
        "description": "Deslizamiento en la vía a Altagracia",
        "longitude": -75.69,
        "latitude": 4.81,
        "reported_by": new_id(),
        **overrides,
    }
    return Incident.create(**data)


# ---------- Dominio de incidentes ----------


@pytest.mark.parametrize(
    ("lon", "lat", "valid"),
    [
        (180.0, 90.0, True),
        (-180.0, -90.0, True),
        (180.0001, 0.0, False),
        (0.0, 90.0001, False),
        (-180.0001, 0.0, False),
        (0.0, -90.0001, False),
    ],
)
def test_limites_de_coordenadas_del_incidente(lon, lat, valid):
    if valid:
        assert _incident(longitude=lon, latitude=lat).status is IncidentStatus.REPORTED
    else:
        with pytest.raises(ValidationError, match="Coordenadas"):
            _incident(longitude=lon, latitude=lat)


@pytest.mark.parametrize(
    ("description", "valid"), [("abcd", False), ("  abcd  ", False), ("abcde", True)]
)
def test_limite_de_5_caracteres_en_descripcion(description, valid):
    if valid:
        assert _incident(description=description).description == "abcde"
    else:
        with pytest.raises(ValidationError):
            _incident(description=description)


def test_transicion_al_mismo_estado_es_rechazada():
    incident = _incident()
    with pytest.raises(ValidationError, match="ya se encuentra"):
        incident.transition_status(new_status=IncidentStatus.REPORTED, changed_by=new_id())
    assert incident.history == []


def test_transicion_valida_registra_historial():
    incident, inspector = _incident(), new_id()
    incident.transition_status(
        new_status=IncidentStatus.IN_REVIEW, changed_by=inspector, notes="Visita técnica"
    )
    [entry] = incident.history
    assert (entry.previous_status, entry.new_status) == (
        IncidentStatus.REPORTED,
        IncidentStatus.IN_REVIEW,
    )
    assert entry.changed_by == inspector


# ---------- Mapeo Mongo tolerante ----------


def test_repositorio_persiste_asignado_y_fecha_de_actualizacion(db):
    repo = MongoIncidentRepository(db)
    incident = _incident()
    incident.assigned_to = new_id()
    incident.updated_at = None  # p. ej. entidad reconstruida sin fecha de actualización

    repo.save(incident)

    assert incident.updated_at is not None  # save() la completa
    doc = db[COLLECTION].find_one()
    assert isinstance(doc["_id"], ObjectId)
    loaded = repo.get_by_id(incident.id)
    assert loaded.assigned_to == incident.assigned_to


def test_documento_sin_ubicacion_usa_coordenadas_por_defecto(db):
    oid = ObjectId()
    db[COLLECTION].insert_one(
        {
            "_id": oid,
            "caseId": "INC-LEGACY-1",
            "type": "INUNDACION",
            "severity": "MEDIA",
            "status": "REPORTADO",
            "description": "Registro antiguo sin geometría",
            "reportedBy": str(new_id()),
            "createdAt": None,
        }
    )
    loaded = MongoIncidentRepository(db).get_by_id(str(oid))
    assert (loaded.longitude, loaded.latitude) == (0.0, 0.0)


# ---------- Índices: migración de índices legacy no-sparse ----------


def test_ensure_indexes_reemplaza_indice_legacy_no_sparse():
    database = mongomock.MongoClient()["idx_test"]
    database[COLLECTION].create_index("case_number", unique=True, name="uq_incidents_case_number")
    assert not database[COLLECTION].index_information()["uq_incidents_case_number"].get("sparse")

    ensure_indexes(database)

    info = database[COLLECTION].index_information()
    assert info["uq_incidents_case_number"]["sparse"] is True
    assert info["uq_incidents_caseId"]["sparse"] is True


def test_ensure_indexes_es_idempotente():
    database = mongomock.MongoClient()["idx_test"]
    ensure_indexes(database)
    ensure_indexes(database)
    assert "uq_incidents_case_number" in database[COLLECTION].index_information()


# ---------- Habitabilidad (fieldwork) ----------


def _inspection(**overrides) -> PropertyInspection:
    data = {
        "property_address": "Carrera 7 # 18-20",
        "neighborhood": "Centro",
        "residents_count": 0,
        "damage_level": DamageLevel.SEVERO,
        "habitability": HabitabilityStatus.EVACUACION,
        "technical_notes": "Fisuras en columnas",
        "longitude": -75.69,
        "latitude": 4.81,
        "inspector_id": new_id(),
        **overrides,
    }
    return PropertyInspection.create(**data)


@pytest.mark.parametrize(
    "overrides",
    [
        {"neighborhood": "C"},
        {"neighborhood": "   "},
        {"residents_count": -1},
        {"longitude": 180.0001},
        {"latitude": -90.0001},
        {"property_address": "Cra7"},
    ],
)
def test_guard_clauses_de_la_inspeccion(overrides):
    with pytest.raises(ValidationError):
        _inspection(**overrides)


def test_limites_validos_de_la_inspeccion():
    inspection = _inspection(residents_count=0, longitude=-180.0, latitude=90.0, neighborhood="Ce")
    assert inspection.residents_count == 0


def test_ensure_indexes_tolera_fallo_al_leer_indices_existentes():
    real = mongomock.MongoClient()["idx_fail"][COLLECTION]

    class _SinPermisoParaListar:
        def __getattr__(self, name):
            return getattr(real, name)

        def index_information(self):
            raise RuntimeError("sin permisos para listar índices")

    ensure_indexes({COLLECTION: _SinPermisoParaListar()})
    assert "uq_incidents_caseId" in real.index_information()
