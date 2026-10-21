"""Identificadores de entidades.

MongoDB usa ObjectId (24 caracteres hexadecimales). En el DOMINIO el id es un
`str` con ese mismo formato: así el dominio no importa `bson` (detalle técnico)
y la capa infrastructure solo hace `ObjectId(id)` al guardar y `str(_id)` al leer.
"""

import secrets


class EntityId(str):
    """Identificador de entidad compatible con str y con API de EntityId."""

    @classmethod
    def generate(cls) -> "EntityId":
        """Genera un nuevo EntityId compatible con ObjectId (12 bytes en hexadecimal)."""
        return cls(secrets.token_hex(12))

    @property
    def value(self) -> str:
        """Devuelve el valor en formato string del identificador."""
        return str(self)


def new_id() -> EntityId:
    """Genera un id válido como ObjectId (12 bytes aleatorios en hexadecimal)."""
    return EntityId.generate()
