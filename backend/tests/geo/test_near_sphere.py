"""$nearSphere contra MongoDB real. Se omite si no hay MONGO_TEST_URI."""
from prevenred.geo.infrastructure.indexes import ensure_indexes as map_indexes
from prevenred.geo.infrastructure.nearby import find_layers_near
from prevenred.incidents.infrastructure.indexes import ensure_indexes as incident_indexes
from prevenred.incidents.infrastructure.nearby import find_incidents_near

_PEREIRA = (-75.696, 4.813)
_LEJOS = (-74.08, 4.71)


def test_incidentes_cerca_usan_near_sphere(real_db):
    incident_indexes(real_db)
    real_db["incidents"].insert_many([
        {"type": "VIA_BLOQUEADA", "location": {"type": "Point", "coordinates": list(_PEREIRA)}},
        {"type": "DESLIZAMIENTO", "location": {"type": "Point", "coordinates": list(_LEJOS)}},
    ])
    indexes = real_db["incidents"].index_information()
    assert "ix_incidents_location_2dsphere" in indexes

    found = find_incidents_near(real_db, _PEREIRA[0], _PEREIRA[1], 2_000)
    assert [item["type"] for item in found] == ["VIA_BLOQUEADA"]


def test_capas_cerca_usan_near_sphere(real_db):
    map_indexes(real_db)
    real_db["map_layers"].insert_many([
        {"name": "centro", "geometry": {"type": "Point", "coordinates": list(_PEREIRA)}},
        {"name": "bogota", "geometry": {"type": "Point", "coordinates": list(_LEJOS)}},
    ])
    indexes = real_db["map_layers"].index_information()
    assert "ix_map_layers_geometry_2dsphere" in indexes

    found = find_layers_near(real_db, _PEREIRA[0], _PEREIRA[1], 2_000)
    assert [item["name"] for item in found] == ["centro"]
