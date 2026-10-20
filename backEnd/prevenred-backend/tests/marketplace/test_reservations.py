"""Pruebas de `marketplace`: choques de fechas y estados de la reserva (CU-13/14/15)."""
from datetime import UTC, datetime, timedelta

import pytest
from bson import ObjectId

from prevenred.marketplace.domain.entities import Reservation, ToolTransaction
from prevenred.marketplace.infrastructure.mongo_marketplace_repository import (
    MongoReservationRepository,
)
from prevenred.shared.domain.errors import ValidationError

OWNER, REQUESTER = str(ObjectId()), str(ObjectId())
#: Herramienta ficticia con id válido: `to_reference` convierte a ObjectId al guardar.
TOOL = str(ObjectId())
START = datetime(2026, 10, 20, 8, tzinfo=UTC)


def _reservation(tool_id: str, start: datetime = START, days: int = 3, **extra) -> Reservation:
    return Reservation(
        tool_id=tool_id,
        requester_id=REQUESTER,
        owner_id=OWNER,
        start_date=start,
        end_date=start + timedelta(days=days),
        cost=15000,
        **extra,
    )


# ----------------------------------------------------------------- dominio
def test_fecha_final_debe_ser_posterior():
    with pytest.raises(ValidationError):
        _reservation(TOOL, days=0)


def test_bordes_no_chocan_la_entrega_es_el_mismo_dia():
    reservation = _reservation(TOOL)
    # Empieza justo cuando termina la otra: no hay conflicto.
    assert not reservation.overlaps(
        reservation.end_date, reservation.end_date + timedelta(days=2)
    )
    # Se cruza un solo día: sí hay conflicto.
    assert reservation.overlaps(START + timedelta(days=1), START + timedelta(days=5))


def test_solo_ocupan_calendario_las_reservas_activas():
    assert _reservation(TOOL).blocks_calendar is True
    assert _reservation(TOOL, status="RECHAZADA").blocks_calendar is False
    assert _reservation(TOOL, status="DEVUELTA").blocks_calendar is False


def test_no_se_aprueba_dos_veces():
    reservation = _reservation(TOOL)
    reservation.approve()
    with pytest.raises(ValidationError):
        reservation.approve()


def test_no_se_devuelve_lo_que_no_se_entrego():
    with pytest.raises(ValidationError):
        _reservation(TOOL).mark_returned(datetime.now(UTC))


def test_operacion_no_permite_autocompra():
    with pytest.raises(ValidationError):
        ToolTransaction(
            buyer_id=OWNER, seller_id=OWNER, item_id=TOOL, type="VENTA", amount=1
        )


# ------------------------------------------------------------ repositorio
def test_consulta_de_choques_ignora_reservas_canceladas(db):
    # `uq_reservations_request` impide dos reservas del mismo solicitante con
    # `createdAt` idéntico, así que cada una se crea en un instante distinto.
    tool, repo = TOOL, MongoReservationRepository(db)
    active = _reservation(tool)
    cancelled = _reservation(tool, status="CANCELADA", created_at=START + timedelta(seconds=1))
    repo.add(active)
    repo.add(cancelled)

    blocking = repo.list_blocking_between(
        tool, active.start_date + timedelta(days=1), active.end_date + timedelta(days=1)
    )
    assert [r.id for r in blocking] == [active.id]


def test_consulta_de_choques_por_fuera_del_rango_no_devuelve_nada(db):
    tool, repo = TOOL, MongoReservationRepository(db)
    repo.add(_reservation(tool))

    later = START + timedelta(days=30)
    assert repo.list_blocking_between(tool, later, later + timedelta(days=2)) == []


def test_ciclo_completo_se_persiste(db):
    tool = TOOL
    repo, reservation = MongoReservationRepository(db), _reservation(tool)
    repo.add(reservation)

    reservation.approve()
    reservation.mark_delivered()
    reservation.mark_returned(datetime.now(UTC))
    repo.update(reservation)

    loaded = repo.get_by_id(reservation.id)
    assert loaded.status == "DEVUELTA" and loaded.returned_at is not None
    assert [r.id for r in repo.list_by_requester(REQUESTER)] == [reservation.id]
    assert [r.id for r in repo.list_by_owner(OWNER)] == [reservation.id]
