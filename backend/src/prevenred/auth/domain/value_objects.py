"""
Value Objects: valores sin identidad que se validan al crearse.
Si existe un `Email`, ya se sabe que es válido (no hay que revalidar).
"""
import re
from dataclasses import dataclass

from prevenred.shared.domain.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    """Correo electrónico válido y normalizado en minúsculas."""
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValidationError("El correo electrónico no tiene un formato válido.")
        # frozen=True impide asignar normal; object.__setattr__ es el truco estándar.
        object.__setattr__(self, "value", normalized)


def validate_password_strength(plain: str) -> None:
    """Política mínima. La política definitiva está pendiente (O-16, doc 07)."""
    if len(plain) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
