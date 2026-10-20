"""Caja blanca de auditoría: autorización, filtro por recurso y orden cronológico."""

import pytest

from prevenred.audit.application.record_audit import AuditUseCase, RecordAuditCommand
from prevenred.audit.infrastructure.mongo_audit_repository import MongoAuditRepository
from prevenred.identity.domain.role import Role

BASE = "/api/v1/audit/logs"


async def _record(motor_db, resource, action="ACTUALIZAR"):
    return await AuditUseCase(MongoAuditRepository(motor_db)).record_event(
        RecordAuditCommand(
            actor_id="64b7f0c2a1b2c3d4e5f60718",
            action=action,
            resource=resource,
            resource_id="r-1",
            details={"campo": "estado"},
        )
    )


@pytest.mark.parametrize("role", [Role.CIUDADANO, Role.INSPECTOR, Role.TECNICO])
def test_logs_solo_para_administradores(api, act_as, make_user, role):
    act_as(make_user(role))
    assert api.get(BASE).status_code == 403


@pytest.mark.asyncio
async def test_admin_filtra_por_recurso_y_aplica_limite(api, act_as, make_user, motor_db):
    await _record(motor_db, "incidents", action="CREAR")
    ultimo = await _record(motor_db, "INCIDENTS", action="CERRAR")
    await _record(motor_db, "users")
    act_as(make_user(Role.ADMIN))

    todos = api.get(BASE).json()
    assert len(todos) == 3
    assert todos[0]["created_at"] >= todos[-1]["created_at"]  # orden descendente

    incidentes = api.get(BASE, params={"resource": "Incidents"}).json()
    assert {log["action"] for log in incidentes} == {"CREAR", "CERRAR"}
    assert all(log["resource"] == "incidents" for log in incidentes)

    assert len(api.get(BASE, params={"limit": 1}).json()) == 1
    assert ultimo.id in {log["id"] for log in incidentes}


@pytest.mark.parametrize(("limit", "status"), [(0, 422), (1, 200), (200, 200), (201, 422)])
def test_limites_del_parametro_limit(api, act_as, make_user, limit, status):
    act_as(make_user(Role.ADMIN))
    assert api.get(BASE, params={"limit": limit}).status_code == status
