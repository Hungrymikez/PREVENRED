"""
Guardas (value objects primitivos) compartidas por todos los contextos.

Por qué existe: en este proyecto la validación es "schema on write" hecha con
Pydantic y con estas guardas; NO usamos validadores `$jsonSchema` de MongoDB.
Las guardas viven en `shared/domain` para que cualquier entidad pueda invocarlas
desde `__post_init__` sin importar librerías técnicas (regla del guardián DDD).
"""
from datetime import UTC, datetime

from prevenred.shared.domain.errors import ValidationError


def require_utc(value: datetime, field: str) -> datetime:
    """Exige una fecha con zona horaria y la deja en UTC.

    Por qué: en Mongo todas las fechas son UTC. Si el dominio aceptara una fecha
    "ingenua" (sin zona), las comparaciones (bloqueos, retención, vencimientos)
    darían resultados distintos según la máquina. Fallamos cerrado y con un
    mensaje claro (G3).
    """
    if value.tzinfo is None:
        raise ValidationError(f"La fecha '{field}' debe incluir zona horaria (UTC).")
    return value.astimezone(UTC)


def require_one_of(value: object, allowed: tuple, field: str) -> None:
    """Valida que un valor pertenezca a un conjunto cerrado (listas ortogonales fijas).

    No se usan `Literal`/`StrEnum` en los modelos porque el proyecto construye las
    entidades en runtime y esos tipos fallarían al evaluarse.
    """
    if value not in allowed:
        opciones = ", ".join(str(a) for a in allowed)
        raise ValidationError(f"'{field}' debe ser uno de: {opciones}.")


def require_text(value: str, field: str, max_length: int = 2000) -> None:
    """Exige un texto no vacío y con un máximo razonable (evita documentos enormes)."""
    if not value or not value.strip():
        raise ValidationError(f"El campo '{field}' es obligatorio.")
    if len(value) > max_length:
        raise ValidationError(f"El campo '{field}' supera los {max_length} caracteres.")


def require_between(
    value: int | float, minimum: int | float, maximum: int | float, field: str
) -> None:
    """Exige un número dentro de un rango cerrado (p. ej. la escala 1-5 de la encuesta).

    Límites inclusivos: 1 y 5 son respuestas válidas en una escala de 1 a 5.
    """
    if not minimum <= value <= maximum:
        raise ValidationError(f"'{field}' debe estar entre {minimum} y {maximum}.")


def require_unique(values: list[str], field: str) -> None:
    """Exige que una lista no tenga repetidos (p. ej. roles o roles con acceso a un archivo)."""
    if len(set(values)) != len(values):
        raise ValidationError(f"El campo '{field}' no puede tener valores repetidos.")