"""
Configuración leída de variables de entorno / archivo .env.
Así los secretos NO viven en el código (ver .env.example).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de la aplicación leídos de variables de entorno o del archivo .env."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MongoDB (documento 09). Local: docker compose up -d. En la nube: cadena de MongoDB Atlas.
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "pereira_responde"

    # CAMBIAR en producción. Duración de sesión pendiente de definir (O-16, doc 07).
    jwt_secret: str = "cambia-esto-en-produccion-usa-32-bytes-o-mas"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Devuelve los ajustes (se leen una sola vez)."""
    return Settings()
