"""Caja blanca de ayudas: router + repositorio Motor + ramas del algoritmo de matching."""

import pytest

from prevenred.aid.application.manage_aid import (
    ExecuteMatchingCommand,
    ManageAidUseCase,
    _calculate_haversine,
)
from prevenred.aid.domain.aid import AidCategory, AidNeed, AidOffer, AidPriority, DonationMatch
from prevenred.aid.infrastructure.mongo_aid_repository import MongoAidRepository
from prevenred.identity.domain.role import Role
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId

BASE = "/api/v1/aid"
PEREIRA = (-75.6961, 4.8143)


def _need(api, **overrides):
    body = {
        "title": "Agua potable",
        "category": "AGUA",
        "quantity": 10,
        "unit": "litros",
        "priority": "MEDIA",
        "longitude": PEREIRA[0],
        "latitude": PEREIRA[1],
        **overrides,
    }
    return api.post(f"{BASE}/needs", json=body)


def _offer(api, **overrides):
    body = {
        "title": "Bidones de agua",
        "category": "AGUA",
        "quantity": 25,
        "unit": "litros",
        "longitude": PEREIRA[0],
        "latitude": PEREIRA[1],
        **overrides,
    }
    return api.post(f"{BASE}/offers", json=body)


# ---------- Endpoints y persistencia ----------


def test_solicitar_y_ofrecer_ayuda_persisten_en_mongo(api, act_as, make_user, motor_db):
    user = act_as(make_user())
    need = _need(api)
    offer = _offer(api, source_material_id="64b7f0c2a1b2c3d4e5f60718")

    assert need.status_code == offer.status_code == 201
    assert need.json()["requester_id"] == user.id
    assert need.json()["unit"] == "litros"
    assert offer.json()["source_material_id"] == "64b7f0c2a1b2c3d4e5f60718"
    assert motor_db["aid_needs"]._col.count_documents({}) == 1
    stored = motor_db["aid_inventory"]._col.find_one()
    assert stored["location"] == {"type": "Point", "coordinates": list(PEREIRA)}


def test_oferta_sin_material_de_origen_devuelve_none(api, act_as, make_user):
    act_as(make_user())
    assert _offer(api).json()["source_material_id"] is None


def test_matching_por_ciudadano_responde_403(api, act_as, make_user):
    act_as(make_user(Role.CIUDADANO))
    r = api.post(f"{BASE}/matching/run")
    assert r.status_code == 403


def test_matching_end_to_end_marca_ambos_como_emparejados(api, act_as, make_user, motor_db):
    act_as(make_user())
    need_id = _need(api).json()["id"]
    offer_id = _offer(api).json()["id"]
    admin = act_as(make_user(Role.ADMIN))

    r = api.post(f"{BASE}/matching/run")
    assert r.status_code == 200
    [match] = r.json()
    assert (match["need_id"], match["offer_id"]) == (need_id, offer_id)
    assert match["matched_quantity"] == 10  # min(necesidad, oferta)
    assert match["matched_by"] == admin.id
    assert motor_db["aid_needs"]._col.find_one()["status"] == "EMPAREJADO"
    assert motor_db["aid_inventory"]._col.find_one()["status"] == "EMPAREJADO"
    # Segunda corrida: ya no hay pendientes -> lista vacía
    assert api.post(f"{BASE}/matching/run").json() == []


# ---------- Boundary testing de coordenadas ----------


@pytest.mark.parametrize(
    ("lon", "lat", "status"),
    [
        (180.0, 90.0, 201),
        (-180.0, -90.0, 201),
        (180.0001, 0.0, 422),
        (-180.0001, 0.0, 422),
        (0.0, 90.0001, 422),
        (0.0, -90.0001, 422),
    ],
)
def test_limites_de_coordenadas_en_api(api, act_as, make_user, lon, lat, status):
    act_as(make_user())
    assert _need(api, longitude=lon, latitude=lat).status_code == status
    assert _offer(api, longitude=lon, latitude=lat).status_code == status


@pytest.mark.parametrize(("lon", "lat"), [(180.1, 0.0), (0.0, -90.1)])
def test_limites_de_coordenadas_en_dominio(lon, lat):
    common = {"category": AidCategory.AGUA, "quantity": 1, "unit": "u", "longitude": lon}
    with pytest.raises(DomainValidationError):
        AidOffer.create(title="Agua", donor_id=EntityId.generate(), latitude=lat, **common)
    with pytest.raises(DomainValidationError):
        AidNeed.create(
            title="Agua",
            priority=AidPriority.MEDIA,
            requester_id=EntityId.generate(),
            latitude=lat,
            **common,
        )


@pytest.mark.parametrize(("title", "quantity"), [("ab", 1), ("Agua", 0), ("Agua", -1)])
def test_oferta_invalida_en_dominio(title, quantity):
    with pytest.raises(DomainValidationError):
        AidOffer.create(
            title=title,
            category=AidCategory.AGUA,
            quantity=quantity,
            unit="u",
            donor_id=EntityId.generate(),
            longitude=0,
            latitude=0,
        )


@pytest.mark.parametrize("quantity", [0, -5])
def test_match_con_cantidad_no_positiva_es_invalido(quantity):
    with pytest.raises(DomainValidationError):
        DonationMatch.create(
            need_id=EntityId.generate(),
            offer_id=EntityId.generate(),
            matched_quantity=quantity,
            distance_meters=0,
            matched_by=EntityId.generate(),
        )


# ---------- Ramas del algoritmo de matching ----------


def _mk_need(lon=0.0, lat=0.0, priority=AidPriority.MEDIA, category=AidCategory.AGUA):
    return AidNeed.create(
        title="Necesidad",
        category=category,
        quantity=5,
        unit="litros",
        priority=priority,
        requester_id=EntityId.generate(),
        longitude=lon,
        latitude=lat,
    )


def _mk_offer(lon=0.0, lat=0.0, category=AidCategory.AGUA, unit="litros"):
    return AidOffer.create(
        title="Oferta",
        category=category,
        quantity=5,
        unit=unit,
        donor_id=EntityId.generate(),
        longitude=lon,
        latitude=lat,
    )


async def _run(motor_db, admin, needs, offers, max_distance=15000.0):
    repo = MongoAidRepository(motor_db)
    for n in needs:
        await repo.save_need(n)
    for o in offers:
        await repo.save_offer(o)
    return await ManageAidUseCase(repo).run_matching(
        ExecuteMatchingCommand(admin_user=admin, max_distance_meters=max_distance)
    )


@pytest.mark.asyncio
async def test_sin_ofertas_compatibles_se_omite_la_necesidad(motor_db, make_user):
    needs = [_mk_need(category=AidCategory.ALIMENTOS)]
    offers = [_mk_offer(category=AidCategory.AGUA), _mk_offer(unit="galones")]
    assert await _run(motor_db, make_user(Role.ADMIN), needs, offers) == []


@pytest.mark.asyncio
async def test_radio_maximo_es_inclusivo_en_el_limite_exacto(motor_db, make_user):
    offer = _mk_offer(lon=0.01, lat=0.0)
    exact = _calculate_haversine(0.0, 0.0, 0.01, 0.0)
    matches = await _run(motor_db, make_user(Role.ADMIN), [_mk_need()], [offer], exact)
    assert len(matches) == 1
    assert matches[0].distance_meters == round(exact, 2)


@pytest.mark.asyncio
async def test_oferta_justo_fuera_del_radio_no_se_empareja(motor_db, make_user):
    offer = _mk_offer(lon=0.01, lat=0.0)
    exact = _calculate_haversine(0.0, 0.0, 0.01, 0.0)
    assert await _run(motor_db, make_user(Role.ADMIN), [_mk_need()], [offer], exact - 0.01) == []


@pytest.mark.asyncio
async def test_se_elige_la_oferta_mas_cercana(motor_db, make_user):
    far, near = _mk_offer(lon=0.05), _mk_offer(lon=0.001)
    [match] = await _run(motor_db, make_user(Role.ADMIN), [_mk_need()], [far, near])
    assert match.offer_id == near.id


@pytest.mark.asyncio
async def test_prioridad_urgente_gana_la_unica_oferta(motor_db, make_user):
    baja = _mk_need(priority=AidPriority.BAJA)
    urgente = _mk_need(priority=AidPriority.URGENTE)
    [match] = await _run(motor_db, make_user(Role.ADMIN), [baja, urgente], [_mk_offer()])
    assert match.need_id == urgente.id


@pytest.mark.asyncio
async def test_repositorio_filtra_pendientes_por_categoria(motor_db):
    repo = MongoAidRepository(motor_db)
    agua, comida = _mk_need(), _mk_need(category=AidCategory.ALIMENTOS)
    for need in (agua, comida):
        await repo.save_need(need)
    oferta_agua = _mk_offer()
    await repo.save_offer(oferta_agua)
    await repo.save_offer(_mk_offer(category=AidCategory.ROPA))

    assert [n.id for n in await repo.list_pending_needs(AidCategory.ALIMENTOS)] == [comida.id]
    assert [o.id for o in await repo.list_pending_offers(AidCategory.AGUA)] == [oferta_agua.id]
    assert len(await repo.list_pending_needs()) == 2
