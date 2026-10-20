"""Hash de contraseñas con Argon2 (algoritmo recomendado actualmente)."""

from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from prevenred.identity.application.ports import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Implementación de PasswordHasher con Argon2."""

    def __init__(self) -> None:
        self._ph = _Argon2()

    def hash(self, plain: str) -> str:
        """Hash Argon2 con sal aleatoria incluida en el resultado."""
        return self._ph.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        """Devuelve False si la contraseña no coincide o si el hash guardado no es válido."""
        try:
            return self._ph.verify(hashed, plain)
        except (VerifyMismatchError, InvalidHashError):
            return False
