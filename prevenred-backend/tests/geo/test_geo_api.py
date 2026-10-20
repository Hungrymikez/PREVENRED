"""Caja blanca de capas cartográficas: autorización y filtro por categoría."""

from prevenred.identity.domain.role import Role

BASE = "/api/v1/geo/layers"
GEOJSON = {"type": "FeatureCollection", "features": []}


def _create(api, name="Zonas de riesgo", category="ZONAS_RIESGO"):
    return api.post(BASE, json={"name": name, "category": category, "geojson_data": GEOJSON})


def test_crear_capa_sin_ser_admin_responde_403(api, act_as, make_user):
    act_as(make_user(Role.INSPECTOR))
    r = _create(api)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_admin_crea_capas_y_se_listan_por_categoria(api, act_as, make_user):
    act_as(make_user(Role.ADMIN))
    inundacion = _create(api)
    cuencas = _create(api, name="Cuencas", category="CUENCAS_HIDRICAS")
    assert inundacion.status_code == cuencas.status_code == 201

    todas = api.get(BASE).json()
    assert {c["id"] for c in todas} == {inundacion.json()["id"], cuencas.json()["id"]}

    filtradas = api.get(BASE, params={"category": "CUENCAS_HIDRICAS"}).json()
    assert [c["name"] for c in filtradas] == ["Cuencas"]


def test_capa_con_categoria_desconocida_responde_422(api, act_as, make_user):
    act_as(make_user(Role.ADMIN))
    assert _create(api, category="NO_EXISTE").status_code == 422


def test_geojson_sin_features_es_rechazado_por_el_dominio(api, act_as, make_user):
    act_as(make_user(Role.ADMIN))
    r = api.post(BASE, json={"name": "Capa", "category": "RED_VIAL", "geojson_data": {}})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
