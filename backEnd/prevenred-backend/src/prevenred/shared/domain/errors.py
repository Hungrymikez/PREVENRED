"""
Errores de dominio.

El dominio y la capa de aplicación NUNCA importan FastAPI, por eso no lanzan
HTTPException. Lanzan estos errores y la capa `interface` los traduce a
códigos HTTP (ver shared/interface/error_handlers.py).

Regla del doc 05 (G3): los mensajes deben ser claros y accionables, sin
exponer datos técnicos ni personales.
"""


class DomainError(Exception):
    """Base de todos los errores de negocio."""

    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    """Datos inválidos o incompletos (excepción E2 de las fichas)."""
    code = "validation_error"


class ConflictError(DomainError):
    """El recurso ya existe, p. ej. correo ya registrado (E1 de CU-01)."""
    code = "conflict"


class NotFoundError(DomainError):
    """El recurso pedido no existe."""
    code = "not_found"


class UnauthorizedError(DomainError):
    """Credenciales o sesión inválidas."""
    code = "unauthorized"


class ForbiddenError(DomainError):
    """Autenticado, pero sin permiso para esta acción (RBAC, RF-03)."""
    code = "forbidden"


class TooManyAttemptsError(DomainError):
    """Bloqueo temporal por intentos repetidos (RNF-14)."""
    code = "too_many_attempts"


class StorageError(DomainError):
    """Un servicio externo (almacenamiento, push/SMS) no respondió (G4: degradación controlada)."""
    code = "storage_error"

