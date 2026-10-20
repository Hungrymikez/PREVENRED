"""
Value Objects: valores sin identidad que se validan al crearse.
Si existe un `Email`, ya se sabe que es válido (no hay que revalidar).
"""
import re
import secrets
from dataclasses import dataclass

from prevenred.shared.domain.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#: Código de un solo uso de 6 dígitos (el mecanismo concreto lo define el doc 07).
_CODE_LENGTH = 6


@dataclass(frozen=True)
class Email:
    """Correo electrónico válido y normalizado en minúsculas.

    Guarda SOLO el texto (`value`). Es a propósito: así el repositorio puede
    recuperar un correo desde Mongo con `Email.desde(doc["email"])` sin importar
    `bson` ni Pydantic, y la regla "un correo válido siempre está normalizado"
    se cumple también al leer de la base.
    """
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValidationError("El correo electrónico no tiene un formato válido.")
        # frozen=True impide asignar normal; object.__setattr__ es el truco estándar.
        object.__setattr__(self, "value", normalized)

    @classmethod
    def desde(cls, texto: str | None) -> "Email | None":
        """Devuelve el correo normalizado, o None si no hay texto (campo opcional)."""
        return cls(texto) if texto else None

    def __str__(self) -> str:
        """Permite usar el value object como texto en logs y documentos."""
        return self.value


def validate_password_strength(plain: str) -> None:
    """Política mínima. La política definitiva está pendiente (O-16, doc 07)."""
    if len(plain) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")


#: Mecanismos del segundo factor. El doc 07 define cuál se implementa primero;
#: aquí sólo se enumeran para que el dominio valide lo que llega de la interfaz.
SECOND_FACTOR_METHODS = ("TOTP", "SMS", "EMAIL")


@dataclass(frozen=True)
class SecondFactorMethod:
    """Mecanismo con el que el administrador entrega el segundo factor (CU-03 paso 2).

    Es un value object y no un `Enum` porque viaja y se guarda como texto
    (`"TOTP"`), igual que los códigos de rol: así no hay que traducirlo al leer
    de Mongo ni al exponerlo por HTTP.
    """
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if normalized not in SECOND_FACTOR_METHODS:
            opciones = ", ".join(SECOND_FACTOR_METHODS)
            raise ValidationError(f"El segundo factor debe ser uno de: {opciones}.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        """Permite usar el value object como texto en logs y documentos."""
        return self.value


@dataclass(frozen=True)
class OneTimeCode:
    """Código de un solo uso del segundo factor (CU-03 paso 3).

    Por qué un value object: un código válido SIEMPRE son 6 dígitos, y comparar
    nunca debe filtrar cuántos dígitos acertó. `mismo_valor_que` usa
    `secrets.compare_digest` (comparación de tiempo constante); `==` compara
    igualdad de valores normalmente y no se usa para validar entradas.
    """
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) != _CODE_LENGTH or not normalized.isdigit():
            raise ValidationError(f"El código debe tener {_CODE_LENGTH} dígitos.")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def generate(cls) -> "OneTimeCode":
        """Genera un código con `secrets` (criptográficamente seguro, no `random`).

        El código generado viaja al administrador (app/SMS); en la entidad solo
        se guarda su hash, igual que con los enlaces de recuperación (CU-02 A2).
        """
        return cls(f"{secrets.randbelow(10 ** _CODE_LENGTH):0{_CODE_LENGTH}d}")

    @classmethod
    def parse(cls, texto: str | None) -> "OneTimeCode | None":
        """Interpreta un texto (p. ej. el que envió el administrador); None si es inválido.

        Se usa en la verificación: un texto mal formado debe contar como código
        incorrecto (intento fallido), NO reventar con un error de validación que
        se pueda distinguir del código equivocado.
        """
        try:
            return cls(texto or "")
        except ValidationError:
            return None

    def mismo_valor_que(self, other: "OneTimeCode | None") -> bool:
        """Compara en tiempo constante: el tiempo no revela cuántos dígitos coinciden."""
        if other is None:
            return False
        return secrets.compare_digest(self.value, other.value)

    def __str__(self) -> str:
        """Permite usar el value object como texto en logs y documentos."""
        return self.value
