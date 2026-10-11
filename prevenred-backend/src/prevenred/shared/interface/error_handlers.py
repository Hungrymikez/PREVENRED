"""
Traduce errores de dominio a respuestas HTTP con un formato uniforme:
    {"error": {"code": "conflict", "message": "..."}}
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from prevenred.shared.domain import errors as e

_STATUS = {
    e.ValidationError: 422,
    e.ConflictError: 409,
    e.NotFoundError: 404,
    e.UnauthorizedError: 401,
    e.ForbiddenError: 403,
    e.TooManyAttemptsError: 429,
}


def register_error_handlers(app: FastAPI) -> None:
    """Instala el traductor de errores de dominio a respuestas HTTP."""

    @app.exception_handler(e.DomainError)
    async def _handle(_: Request, exc: e.DomainError) -> JSONResponse:
        status = _STATUS.get(type(exc), 400)
        return JSONResponse(
            status_code=status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
