"""
Punto de entrada de la API (composition root).
Ejecutar:  uvicorn prevenred.main:app --reload --app-dir src
Docs interactivas:  http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from prevenred.auth.infrastructure.indexes import ensure_indexes as identity_indexes
from prevenred.auth.interface.router import router as identity_router
from prevenred.geo.infrastructure.indexes import ensure_indexes as map_indexes
from prevenred.incidents.infrastructure.indexes import ensure_indexes as incident_indexes
from prevenred.services.infrastructure.indexes import ensure_indexes as technician_indexes
from prevenred.shared.infrastructure.config import get_settings
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_db
from prevenred.shared.interface.error_handlers import register_error_handlers
from prevenred.volunteering.infrastructure.indexes import ensure_indexes as volunteer_indexes

# Cada contexto con colecciones agrega aquí su función de índices (una línea por contexto).
INDEX_INITIALIZERS = [
    identity_indexes,
    incident_indexes,
    map_indexes,
    technician_indexes,
    volunteer_indexes,
]


# Suscriptores de eventos de dominio: cada contexto que reacciona a eventos de otro agrega aquí
# una función `register_handlers(bus)`. Ej.: services escucha UserRegistered (CU-01 paso 7).
EVENT_SUBSCRIBERS: list = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = get_db()
    for ensure in INDEX_INITIALIZERS:
        ensure(db)  # idempotente: si el índice ya existe no hace nada
    yield


def create_app() -> FastAPI:
    """Construye la aplicación: manejador de errores, suscriptores de eventos y routers."""
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET no está definido.")
    app = FastAPI(title="PrevenRed API", version="0.2.0", lifespan=lifespan)
    register_error_handlers(app)
    for register_handlers in EVENT_SUBSCRIBERS:
        register_handlers(event_bus)
    app.include_router(identity_router)
    # Cada contexto nuevo agrega aquí su router (una línea por contexto).
    return app


app = create_app()
