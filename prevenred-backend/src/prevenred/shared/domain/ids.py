"""
Identificadores de entidades.

MongoDB usa ObjectId (24 caracteres hexadecimales). En el DOMINIO el id es un
`str` con ese mismo formato: así el dominio no importa `bson` (detalle técnico)
y la capa infrastructure solo hace `ObjectId(id)` al guardar y `str(_id)` al leer.
"""
import secrets

EntityId = str


def new_id() -> EntityId:
    """Genera un id válido como ObjectId (12 bytes aleatorios en hexadecimal)."""
    return secrets.token_hex(12)
