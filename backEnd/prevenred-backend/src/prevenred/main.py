"""
Punto de entrada de la API (composition root).
Ejecutar:  uvicorn prevenred.main:app --reload --app-dir src
Docs interactivas:  http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from prevenred.aid.infrastructure.indexes import ensure_indexes as aid_indexes
from prevenred.fieldwork.infrastructure.indexes import ensure_indexes as fieldwork_indexes
from prevenred.geo.infrastructure.indexes import ensure_indexes as geo_indexes
from prevenred.identity.infrastructure.indexes import ensure_indexes as identity_indexes
from prevenred.identity.interface.router import router as identity_router
from prevenred.incidents.infrastructure.indexes import ensure_indexes as incidents_indexes
from prevenred.marketplace.infrastructure.indexes import ensure_indexes as marketplace_indexes
from prevenred.media.infrastructure.indexes import ensure_indexes as media_indexes
from prevenred.notifications.infrastructure.indexes import ensure_indexes as notifications_indexes
from prevenred.services.infrastructure.indexes import ensure_indexes as services_indexes
from prevenred.shared.application.case_code_generator import CaseCodeGenerator
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.indexes import ensure_indexes as shared_indexes
from prevenred.shared.infrastructure.mongo import get_db
from prevenred.shared.infrastructure.mongo_case_code_generator import MongoCaseCodeGenerator
from prevenred.shared.interface.error_handlers import register_error_handlers
from prevenred.wellbeing.infrastructure.indexes import ensure_indexes as wellbeing_indexes

#: ÚNICA fuente de verdad de los índices: la usan el arranque (`lifespan`) y las
#: pruebas (`tests/conftest.py` importa esta lista). Cada contexto con colecciones
#: agrega aquí su función de índices (una línea por contexto).
INDEX_INITIALIZERS = [
    identity_indexes,
    marketplace_indexes,
    services_indexes,
    wellbeing_indexes,
    fieldwork_indexes,
    incidents_indexes,
    geo_indexes,
    aid_indexes,
    media_indexes,
    notifications_indexes,
    shared_indexes,        # `counters` + unicidad de `caseId` (RF-22)
]


# Suscriptores de eventos de dominio: cada contexto que reacciona a eventos de otro agrega aquí
# una función `register_handlers(bus)`. Ej.: services escucha UserRegistered (CU-01 paso 7).
EVENT_SUBSCRIBERS: list = []


def create_case_code_generator(db=None) -> CaseCodeGenerator:
    """Arma el generador de códigos de caso (RF-22) sobre la base de datos indicada.

    TODO(case-ids): cuando existan los casos de uso que crean reportes, inmuebles y
    necesidades de ayuda (CU-29, CU-17/33, CU-31), inyéctalo igual que los
    repositorios y llama `next_code(CaseKind.INCIDENTE)` / `INMUEBLE` / `AYUDA`
    antes de guardar la entidad, para que `caseId` salga de aquí.
    """
    return MongoCaseCodeGenerator(db if db is not None else get_db())


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = get_db()
    for ensure in INDEX_INITIALIZERS:
        ensure(db)  # idempotente: si el índice ya existe no hace nada
    yield


def create_app() -> FastAPI:
    """Construye la aplicación: manejador de errores, suscriptores de eventos y routers."""
    app = FastAPI(title="PrevenRed API", version="0.2.0", lifespan=lifespan)
    register_error_handlers(app)
    for register_handlers in EVENT_SUBSCRIBERS:
        register_handlers(event_bus)
    app.include_router(identity_router)
    # Generador de códigos de caso (RF-22), disponible para los routers que lo pidan.
    app.state.case_codes = create_case_code_generator()
    # Cada contexto nuevo agrega aquí su router (una línea por contexto).
    return app


app = create_app()

