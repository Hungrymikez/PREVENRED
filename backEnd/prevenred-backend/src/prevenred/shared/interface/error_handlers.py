"""
Traduce errores de dominio y de validación a respuestas HTTP con un formato uniforme:
    {"error": {"code": "conflict", "message": "..."}}
    {"error": {"code": "validation_error", "message": "..."}}

Por qué también los de Pydantic: sin esto la API respondía DOS formatos distintos
(dominio y `{"detail": [...]}` de FastAPI), y un cliente tenía que distinguir cuál
le tocó para leer el mensaje. Ahora todos los errores se leen igual.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from prevenred.shared.domain import errors as e

logger = logging.getLogger(__name__)

_STATUS = {
    e.ValidationError: 422,
    e.ConflictError: 409,
    e.NotFoundError: 404,
    e.UnauthorizedError: 401,
    e.ForbiddenError: 403,
    e.TooManyAttemptsError: 429,
}

#: Tipo de error de Pydantic -> texto en español para el usuario final.
_TYPE_MESSAGES = {
    "missing": "Falta un dato obligatorio",
    "literal_error": "El valor no es una de las opciones permitidas",
    "int_parsing": "Debe ser un número entero",
    "float_parsing": "Debe ser un número",
    "bool_parsing": "Debe ser verdadero o falso",
    "bool_type": "Debe ser verdadero o falso",
    "string_type": "Debe ser un texto",
    "json_invalid": "El cuerpo no es un JSON válido",
}


def _field_name(error: dict) -> str:
    """`body.roles.0` / `query.page` -> el nombre del campo, sin la ubicación."""
    location = [str(part) for part in error.get("loc", ()) if part not in ("body", "query", "path")]
    return ".".join(location)


def _one(error: dict) -> str:
    """Traduce UN error de Pydantic a una frase para el usuario."""
    field = _field_name(error)
    kind = str(error.get("type", ""))
    limit = (error.get("ctx") or {}).get("limit")
    if kind in _TYPE_MESSAGES:
        base = _TYPE_MESSAGES[kind]
    elif "min_length" in kind or kind.endswith("too_short"):
        base = (
            f"Debe tener al menos {limit} caracteres" if limit
            else "El texto es más corto de lo permitido"
        )
    elif "max_length" in kind or kind.endswith("too_long"):
        base = (
            f"Debe tener como máximo {limit} caracteres" if limit
            else "El texto es más largo de lo permitido"
        )
    else:
        # Último recurso: el mensaje de Pydantic (en inglés, pero ya en un formato único).
        base = str(error.get("msg", "El valor no es válido"))
    return f"{field}: {base}." if field else f"{base}."


def _describe(exc: RequestValidationError) -> str:
    """Une todos los errores en UN mensaje (el formato estándar tiene uno solo)."""
    messages = list(dict.fromkeys(_one(err) for err in exc.errors()))   # sin repetidos
    return " ".join(messages) or "Los datos enviados no son válidos."


def register_error_handlers(app: FastAPI) -> None:
    """Instala el traductor de errores de dominio a respuestas HTTP."""

    @app.exception_handler(e.DomainError)
    async def _handle(_: Request, exc: e.DomainError) -> JSONResponse:
        status = _STATUS.get(type(exc), 400)
        return JSONResponse(
            status_code=status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Formato válido y tipos: `422` con el MISMO formato que los errores de dominio."""
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": _describe(exc)}},
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        """Error no previsto: `500` sin filtrar detalles técnicos al cliente (G3)."""
        logger.exception(
            "Error no controlado en %s %s", request.method, request.url.path, exc_info=exc
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Ocurrió un error inesperado. Intenta de nuevo más tarde.",
                }
            },
        )
