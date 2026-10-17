"""Pruebas del contexto `aid`: regla de reserva y escritura atómica del inventario (CU-41/42)."""
import pytest
from bson import ObjectId

from prevenred.aid.domain.entities import AidInventoryItem, AidNeed
from prevenred.aid.infrastructure.mongo_aid_repository import (
    INVENTORY_COLLECTION,
    NEEDS_COLLECTION,
    MongoAidInventoryRepository,
    MongoAidNeedRepository,
)
from prevenred.shared.domain.errors import ValidationError

USER = str(ObjectId())


def _item(quantity=5, **extra) -> AidInventoryItem:
    return AidInventoryItem(
        source_id=USER,
        source_type="MATERIAL",
        type="AGUA",
        quantity=quantity,
        origin_trace="Donación campaña octubre",
        **extra,
    )


def _need(**extra) -> AidNeed:
    return AidNeed(
        type="AGUA",
        description="Se requiere agua potable",
        requested_by=USER,
        quantity=10,
        latitude=4.8133,
        longitude=-75.6961,
        priority="ALTA",
        case_id=f"CASO-{ObjectId()}",
        **extra,
    )


# ----------------------------------------------------------------- dominio
def test_reservar_descuenta_y_agota():
    item = _item(quantity=3)
    item.reserve(2)
    assert (item.quantity, item.available_quantity) == (3, 1)
    item.reserve(1)
    assert item.status == "AGOTADO"


def test_no_se_puede_reservar_mas_de_lo_disponible():  # CU-42
    with pytest.raises(ValidationError):
        _item(quantity=2).reserve(3)


def test_recibir_repone_el_recurso_agotado():
    item = _item(quantity=1)
    item.reserve(1)
    item.receive(4)
    assert item.status == "DISPONIBLE" and item.available_quantity == 4


# ------------------------------------------------------------ repositorio
def test_reserva_atomica_descuenta_stock(db):
    repo = MongoAidInventoryRepository(db)
    item = _item(quantity=4)
    repo.add(item)

    assert repo.reserve_stock(item.id, 3) is True
    assert repo.get_by_id(item.id).available_quantity == 1


def test_reserva_atomica_falla_sin_stock_suficiente(db):
    repo = MongoAidInventoryRepository(db)
    item = _item(quantity=2)
    repo.add(item)

    assert repo.reserve_stock(item.id, 3) is False
    # El inventario queda intacto: no se promete ayuda inexistente.
    assert repo.get_by_id(item.id).available_quantity == 2


def test_reserva_atomica_marca_agotado_y_sale_de_los_disponibles(db):
    repo = MongoAidInventoryRepository(db)
    item = _item(quantity=2)
    repo.add(item)

    assert repo.reserve_stock(item.id, 2) is True
    assert repo.get_by_id(item.id).status == "AGOTADO"
    assert repo.list_available() == []


def test_reserva_rechaza_id_invalido_y_cantidad_cero(db):
    repo = MongoAidInventoryRepository(db)
    assert repo.reserve_stock("no-es-un-id", 1) is False
    assert repo.reserve_stock(str(ObjectId()), 0) is False


def test_update_del_inventario_no_toca_el_origen(db):
    repo = MongoAidInventoryRepository(db)
    item = _item(quantity=2)
    repo.add(item)
    db[INVENTORY_COLLECTION].update_one(
        {"_id": ObjectId(item.id)}, {"$set": {"sourceType": "DONACION"}}
    )

    item.receive(1)
    repo.update(item)

    doc = db[INVENTORY_COLLECTION].find_one({"_id": ObjectId(item.id)})
    assert doc["sourceType"] == "DONACION" and doc["availableQuantity"] == 3


def test_necesidad_se_guarda_con_punto_geojson_y_se_busca_por_solicitante(db):
    repo = MongoAidNeedRepository(db)
    need = _need()
    repo.add(need)

    doc = db[NEEDS_COLLECTION].find_one({"_id": ObjectId(need.id)})
    assert doc["location"] == {"type": "Point", "coordinates": [-75.6961, 4.8133]}

    loaded = repo.get_by_id(need.id)
    assert (loaded.latitude, loaded.longitude) == (4.8133, -75.6961)
    assert [n.id for n in repo.list_by_requester(USER)] == [need.id]
    assert [n.id for n in repo.list_open()] == [need.id]
