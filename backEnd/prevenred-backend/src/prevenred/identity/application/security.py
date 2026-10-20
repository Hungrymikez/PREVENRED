"""
Servicios técnicos de seguridad que orquestan los casos de uso de identity.

- `hash_one_time_code`: el código del segundo factor (CU-03) y la contraseña
  temporal (CU-08 A1) se guardan HASHED, nunca en claro.
- `temporary_password`: credenciales iniciales de una cuenta creada por un
  Administrador; son aleatorias y se muestran UNA sola vez.

Se usa SHA-256 para los códigos de un solo uso: son cortos (6 dígitos), viven
minutos y los intentos ya están limitados por el dominio (MFA_MAX_ATTEMPTS), así
que no hace falta un KDF lento como Argon2 —el bloqueo por intentos es lo que
impide la fuerza bruta. Las CONTRASEÑAS sí usan Argon2 (`PasswordHasher`).
"""
import hashlib
import secrets
import string

#: Longitud de la contraseña temporal (CU-08 A1). Aleatoria, no memorizable.
TEMP_PASSWORD_LENGTH = 16
_ALPHABET = string.ascii_letters + string.digits


def hash_one_time_code(code: str) -> str:
    """Devuelve el hash del código ya normalizado (sin espacios ni guiones)."""
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def temporary_password() -> str:
    """Genera una contraseña temporal aleatoria (A1: se cambia en el primer acceso).

    `secrets.choice` es criptográficamente seguro: una contraseña predecible
    anularía el sentido de que la cuenta la entregue el sistema. Se garantiza al
    menos una minúscula, una mayúscula y un dígito para cumplir la política.
    """
    while True:
        candidate = "".join(secrets.choice(_ALPHABET) for _ in range(TEMP_PASSWORD_LENGTH))
        if (
            any(c.islower() for c in candidate)
            and any(c.isupper() for c in candidate)
            and any(c.isdigit() for c in candidate)
        ):
            return candidate