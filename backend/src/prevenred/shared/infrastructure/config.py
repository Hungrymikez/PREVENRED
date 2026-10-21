"""
Configuración leída de variables de entorno / archivo .env.
Así los secretos NO viven en el código (ver .env.example).
"""

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT_MARKERS = ("cambia-esto", "pon-aqui", "changeme", "secret")


class Settings(BaseSettings):
    """Ajustes de la aplicación leídos de variables de entorno o del archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    # MongoDB (documento 09). Local: docker compose up -d. En la nube: cadena de MongoDB Atlas.
    # Soporta MONGO_URI o MONGODB_URI, y MONGO_DB_NAME o MONGODB_DB_NAME.
    mongo_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("mongo_uri", "mongodb_uri"),
    )
    mongo_db_name: str = Field(
        default="PrevenRED2",
        validation_alias=AliasChoices("mongo_db_name", "mongodb_db_name"),
    )

    # Sin valor por defecto: si falta JWT_SECRET, Pydantic rechaza el arranque.
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # production exige MFA a administradores, salvo que MFA_ENABLED sea false.
    environment: str = "production"
    mfa_enabled: bool = True

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_es_obligatorio(cls, value: str) -> str:
        """Rechaza un secreto ausente, corto o de ejemplo."""
        secret = value.strip()
        lowered = secret.lower()
        insecure = any(
            lowered.startswith(marker) or lowered == marker for marker in _INSECURE_JWT_MARKERS
        )
        if len(secret) < 32 or insecure:
            raise ValueError(
                "JWT_SECRET debe estar en .env: al menos 32 caracteres y sin un valor de ejemplo."
            )
        return secret

    @property
    def admin_login_requires_mfa(self) -> bool:
        """CU-03. En development, o con MFA_ENABLED=false, el administrador puede entrar."""
        if not self.mfa_enabled:
            return False
        return self.environment.strip().lower() != "development"


@lru_cache
def get_settings() -> Settings:
    """Devuelve los ajustes (se leen una sola vez). Falla si JWT_SECRET no es válido."""
    return Settings()
