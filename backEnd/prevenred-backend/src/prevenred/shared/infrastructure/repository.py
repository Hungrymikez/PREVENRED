"""
Base de los repositorios PyMongo (sin ODM).

Por qué existe: cada repositorio repetía la misma traducción documento <-> entidad
(convertir `_id` y las referencias a `ObjectId` al escribir, volver a `str` al leer,
normalizar fechas a UTC, aplicar `$set` en lugar de reemplazar el documento y
traducir `DuplicateKeyError` a `ConflictError`). Aquí eso se escribe UNA vez.

Una subclase solo declara:
  - `collection`  nombre de la colección (ver docs/db/<coleccion>.md)
  - `to_document` entidad -> documento completo (solo al insertar)
  - `to_entity`   documento -> entidad
  - `updates`     entidad -> dict con los campos que el contexto puede cambiar
y, si hace falta, sobrescribe `add`, `update` o añade consultas propias.

Regla del proyecto (doc 09): el id en el dominio es `str`; `ObjectId` solo aparece
en infrastructure.
"""
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from prevenred.shared.domain.errors import ConflictError

T = TypeVar("T")


def to_object_id(value: str | None) -> ObjectId | None:
    """`str` del dominio -> `ObjectId` de Mongo. None si el valor no es un id válido.

    Devolver None (en vez de lanzar) permite responder "no existe" a un id mal
    formado, sin filtrar detalles técnicos al usuario (G3).
    """
    if value is None or not ObjectId.is_valid(value):
        return None
    return ObjectId(value)


def to_reference(value: str | None) -> ObjectId | None:
    """Id de OTRO documento al que se apunta (`userId`, `ownerId`, `propertyId`...)."""
    return to_object_id(value)



def to_id_str(value: Any) -> str | None:
    """`ObjectId` (o `str`) de Mongo -> `str` del dominio."""
    if value is None:
        return None
    return str(value)


def utc_aware(value: datetime | None) -> datetime | None:
    """Mongo devuelve fechas sin zona si el cliente no es `tz_aware`; las dejamos en UTC."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class BaseMongoRepository(ABC, Generic[T]):
    """Repositorio PyMongo genérico: traduce documento <-> entidad y evita repetir código."""

    collection: str = ""

    def __init__(self, db: Database) -> None:
        if not self.collection:
            raise ValueError("La subclase debe declarar el nombre de la colección.")
        self._col = db[self.collection]

    # ---- Lo que declara cada repositorio ----
    @abstractmethod
    def to_document(self, entity: T) -> dict:
        """Entidad -> documento completo para insertar (incluye `_id`)."""

    @abstractmethod
    def to_entity(self, document: dict) -> T:
        """Documento de Mongo -> entidad de dominio (ids como str, fechas en UTC)."""

    @abstractmethod
    def updates(self, entity: T) -> dict:
        """Campos que este contexto puede cambiar (se aplican con `$set`)."""

    # ---- Comportamiento común ----
    def get_by_id(self, entity_id: str) -> T | None:
        """Busca por id; devuelve None si el id no tiene formato válido o no existe."""
        oid = to_object_id(entity_id)
        if oid is None:
            return None
        document = self._col.find_one({"_id": oid})
        return self.to_entity(document) if document else None

    def add(self, entity: T) -> None:
        """Inserta la entidad. Un índice único la protege de duplicados simultáneos."""
        try:
            self._col.insert_one(self.to_document(entity))
        except DuplicateKeyError as exc:
            raise self.conflict_message() from exc

    def update(self, entity: T) -> None:
        """Actualiza solo los campos del contexto (`$set`), nunca el documento entero.

        Si no hay nada que actualizar no hace la escritura: con un `$set` vacío
        Mongo fallaría.
        """
        fields = dict(self.updates(entity))
        if not fields:
            return
        identity = getattr(entity, "id", None)
        if identity is None:
            raise ValueError("No se puede actualizar una entidad sin id.")
        try:
            self._col.update_one({"_id": ObjectId(identity)}, {"$set": fields})
        except DuplicateKeyError as exc:
            raise self.conflict_message() from exc

    def delete(self, entity_id: str) -> bool:
        """Borra el documento. True si existía (lo usa la retención de datos, RN-06)."""
        oid = to_object_id(entity_id)
        if oid is None:
            return False
        return self._col.delete_one({"_id": oid}).deleted_count == 1

    def exists(self, entity_id: str) -> bool:
        """True si el documento existe (consulta liviana, sin traerlo completo)."""
        oid = to_object_id(entity_id)
        return oid is not None and self._col.count_documents({"_id": oid}, limit=1) == 1

    @staticmethod
    def conflict_message() -> ConflictError:
        """Error a lanzar cuando un índice único impide guardar (mensaje por defecto)."""
        return ConflictError("Ese registro ya existe.")
