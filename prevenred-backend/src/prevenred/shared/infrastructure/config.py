"""
Configuración leída de variables de entorno / archivo .env.
Así los secretos NO viven en el código (ver .env.example).
"""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de la aplicación leídos de variables de entorno o del archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    # MongoDB. Soporta MONGO_URI o MONGODB_URI, y MONGO_DB_NAME o MONGODB_DB_NAME
    mongo_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("mongo_uri", "mongodb_uri"),
    )
    mongo_db_name: str = Field(
        default="pereira_responde",
        validation_alias=AliasChoices("mongo_db_name", "mongodb_db_name"),
    )

    # CAMBIAR en producción. Duración de sesión pendiente de definir (O-16, doc 07).
    jwt_secret: str = "cambia-esto-en-produccion-usa-32-bytes-o-mas"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Devuelve los ajustes (se leen una sola vez)."""
    return Settings()
