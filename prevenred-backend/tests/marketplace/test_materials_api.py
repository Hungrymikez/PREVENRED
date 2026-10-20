"""Caja blanca de SegundaVida: router + repositorio Motor + búsqueda geoespacial ($nearSphere)."""

import pytest

from tests.async_mongo import haversine_meters

BASE = "/api/v1/marketplace/materials"
ORIGIN = (-75.6961, 4.8143)  # Plaza de Bolívar, Pereira


def _publish(api, **overrides):
    body = {
        "title": "Tejas de barro",
        "description": "  Sobrantes de obra  ",
        "category": "CONSTRUCCION",
        "offer_type": "DONACION",
        "condition": "BUENO",
        "quantity": 30,
        "unit": "unidades",
        "longitude": ORIGIN[0],
        "latitude": ORIGIN[1],
        **overrides,
    }
    return api.post(BASE, json=body)


def _search(api, **params):
    query = {"longitude": ORIGIN[0], "latitude": ORIGIN[1], **params}
    return api.get(f"{BASE}/search", params=query)


def test_publicar_y_consultar_material(api, act_as, make_user):
    owner = act_as(make_user())
    created = _publish(api)
    assert created.status_code == 201
    body = created.json()
    assert body["owner_id"] == owner.id
    assert body["description"] == "Sobrantes de obra"
    assert body["price"] == 0.0  # donación => precio 0

    fetched = api.get(f"{BASE}/{body['id']}")
    assert fetched.status_code == 200
    # BSON guarda milisegundos: se compara todo menos created_at
    assert {**fetched.json(), "created_at": None} == {**body, "created_at": None}


def test_material_inexistente_responde_404(api):
    r = api.get(f"{BASE}/64b7f0c2a1b2c3d4e5f60718")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_venta_sin_precio_es_rechazada_por_el_dominio(api, act_as, make_user):
    act_as(make_user())
    r = _publish(api, offer_type="VENTA", price=None)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_busqueda_filtra_por_radio_y_ordena_por_cercania(api, act_as, make_user):
    act_as(make_user())
    lejos = _publish(api, title="Lejos", longitude=ORIGIN[0] + 0.05).json()  # ~5.5 km
    cerca = _publish(api, title="Cerca", longitude=ORIGIN[0] + 0.005).json()  # ~550 m

    r = _search(api, radius_meters=10000)
    assert [m["id"] for m in r.json()] == [cerca["id"], lejos["id"]]

    r = _search(api, radius_meters=1000)
    assert [m["id"] for m in r.json()] == [cerca["id"]]


def test_busqueda_combina_filtros_de_categoria_y_tipo_de_oferta(api, act_as, make_user):
    act_as(make_user())
    _publish(api, title="Madera donada", category="MADERA")
    venta = _publish(api, title="Madera vendida", category="MADERA", offer_type="VENTA", price=5)
    _publish(api, title="Tubos", category="PLOMERIA", offer_type="VENTA", price=5)

    r = _search(api, category="MADERA", offer_type="VENTA")
    assert [m["id"] for m in r.json()] == [venta.json()["id"]]


def test_busqueda_excluye_materiales_inactivos_y_respeta_limit(api, act_as, make_user, motor_db):
    act_as(make_user())
    ids = [_publish(api, title=f"Material {i}").json()["id"] for i in range(3)]
    motor_db["materials"]._col.update_one({"_id": ids[0]}, {"$set": {"is_active": False}})

    assert len(_search(api).json()) == 2
    assert len(_search(api, limit=1).json()) == 1


@pytest.mark.parametrize(
    ("params", "status"),
    [
        ({"radius_meters": 99.9}, 422),
        ({"radius_meters": 100}, 200),
        ({"radius_meters": 50000}, 200),
        ({"radius_meters": 50000.1}, 422),
        ({"limit": 0}, 422),
        ({"limit": 101}, 422),
        ({"longitude": 180.0001}, 422),
        ({"latitude": -90.0001}, 422),
    ],
)
def test_limites_de_parametros_de_busqueda(api, params, status):
    assert _search(api, **params).status_code == status


def test_radio_minimo_de_100m_incluye_justo_el_borde(api, act_as, make_user):
    act_as(make_user())
    # Desplazamiento en latitud de ~99.6 m: dentro del radio mínimo de 100 m
    dentro = _publish(api, latitude=ORIGIN[1] + 0.000896).json()
    _publish(api, latitude=ORIGIN[1] + 0.00091)  # ~101.2 m: fuera
    assert haversine_meters(*ORIGIN, ORIGIN[0], ORIGIN[1] + 0.000896) < 100
    assert [m["id"] for m in _search(api, radius_meters=100).json()] == [dentro["id"]]
