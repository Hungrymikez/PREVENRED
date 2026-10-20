"""
Punto de entrada de la API (composition root).
Ejecutar:  uvicorn prevenred.main:app --reload --app-dir src
Docs interactivas:  http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from prevenred.aid.infrastructure.mongo_aid_repository import MongoAidRepository
from prevenred.aid.interface.router import router as aid_router
from prevenred.audit.infrastructure.mongo_audit_repository import MongoAuditRepository
from prevenred.audit.interface.router import router as audit_router
from prevenred.fieldwork.infrastructure.indexes import ensure_indexes as fieldwork_indexes
from prevenred.fieldwork.interface.router import router as fieldwork_router
from prevenred.geo.interface.router import router as geo_router
from prevenred.identity.infrastructure.indexes import ensure_indexes as identity_indexes
from prevenred.identity.interface.router import router as identity_router
from prevenred.incidents.infrastructure.indexes import ensure_indexes as incidents_indexes
from prevenred.incidents.interface.router import router as incidents_router
from prevenred.marketplace.infrastructure.mongo_material_repository import (
    MongoMaterialRepository,
)
from prevenred.marketplace.interface.router import router as marketplace_router
from prevenred.media.interface.router import router as media_router
from prevenred.operating_mode.infrastructure.indexes import (
    ensure_indexes as operating_mode_indexes,
)
from prevenred.operating_mode.interface.router import router as operating_mode_router
from prevenred.reporting.interface.router import router as reporting_router
from prevenred.services.infrastructure.mongo_technician_repository import (
    MongoTechnicianRepository,
)
from prevenred.services.interface.router import router as services_router
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_database, get_db
from prevenred.shared.interface.error_handlers import register_error_handlers
from prevenred.volunteering.infrastructure.mongo_volunteer_repository import (
    MongoVolunteerRepository,
)
from prevenred.volunteering.interface.router import router as volunteering_router
from prevenred.wellbeing.infrastructure.mongo_wellbeing_repository import (
    MongoWellbeingRepository,
)
from prevenred.wellbeing.interface.router import router as wellbeing_router

# Cada contexto con colecciones agrega aquí su función de índices (una línea por contexto).
INDEX_INITIALIZERS = [
    identity_indexes,
    operating_mode_indexes,
    incidents_indexes,
    fieldwork_indexes,
]

# Contextos asíncronos (Motor): cada repositorio declara sus índices en `create_indexes()`.
# Sin esto los índices 2dsphere no existen y las búsquedas $nearSphere fallan en MongoDB real.
ASYNC_INDEX_REPOSITORIES = [
    MongoAidRepository,
    MongoAuditRepository,
    MongoMaterialRepository,
    MongoTechnicianRepository,
    MongoVolunteerRepository,
    MongoWellbeingRepository,
]


async def ensure_async_indexes(database) -> None:
    """Crea (idempotente) los índices de los repositorios asíncronos."""
    for repository_cls in ASYNC_INDEX_REPOSITORIES:
        await repository_cls(database).create_indexes()


# Suscriptores de eventos de dominio: cada contexto que reacciona a eventos de otro agrega aquí
# una función `register_handlers(bus)`. Ej.: services escucha UserRegistered (CU-01 paso 7).
EVENT_SUBSCRIBERS: list = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = get_db()
    for ensure in INDEX_INITIALIZERS:
        ensure(db)  # idempotente: si el índice ya existe no hace nada
    await ensure_async_indexes(get_database())
    yield


def create_app() -> FastAPI:
    """Construye la aplicación: manejador de errores, suscriptores de eventos y routers."""
    app = FastAPI(title="PrevenRed API", version="0.2.0", lifespan=lifespan)
    register_error_handlers(app)
    for register_handlers in EVENT_SUBSCRIBERS:
        register_handlers(event_bus)
    app.include_router(identity_router)
    app.include_router(operating_mode_router)
    app.include_router(incidents_router)
    app.include_router(fieldwork_router)
    app.include_router(marketplace_router, prefix="/api/v1")
    app.include_router(services_router, prefix="/api/v1")
    app.include_router(aid_router, prefix="/api/v1")
    app.include_router(volunteering_router, prefix="/api/v1")
    app.include_router(wellbeing_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(geo_router, prefix="/api/v1")
    app.include_router(media_router, prefix="/api/v1")
    app.include_router(reporting_router, prefix="/api/v1")
    # Cada contexto nuevo agrega aquí su router (una línea por contexto).
    return app


app = create_app()
