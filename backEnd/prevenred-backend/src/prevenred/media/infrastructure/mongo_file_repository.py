"""
Repositorio de metadatos de archivos sobre MongoDB: colección `files` (CU-47).

El binario NO vive en Mongo: vive en el almacenamiento (S3/MinIO) cifrado (RNF-05).
Aquí solo se guarda la referencia segura y quién puede verla (RN-06).
"""
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from prevenred.media.domain.file import StoredFile
from prevenred.media.domain.repositories import FileRepository
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "files"


def _to_entity(d: dict) -> StoredFile:
    """Documento -> StoredFile."""
    link = d.get("linkedTo") or {}
    return StoredFile(
        id=str(d["_id"]),
        owner_id=str(d["ownerId"]),
        file_name=d["fileName"],
        mime_type=d["mimeType"],
        url=d["url"],
        size=int(d.get("size") or 0),
        category=d.get("category", ""),
        access_roles=tuple(d.get("accessRoles") or ()),
        linked_collection=link.get("collection"),
        linked_id=str(link["id"]) if link.get("id") else None,
        encrypted=bool(d.get("encrypted", True)),
        retention_until=utc_aware(d.get("retentionUntil")),
        created_at=utc_aware(d["createdAt"]),
    )


def _to_document(f: StoredFile) -> dict:
    """StoredFile -> documento completo."""
    linked = (
        {"collection": f.linked_collection, "id": to_reference(f.linked_id)}
        if f.linked_collection and f.linked_id
        else None
    )
    return {
        "_id": ObjectId(f.id),
        "ownerId": to_reference(f.owner_id),
        "fileName": f.file_name,
        "mimeType": f.mime_type,
        "url": f.url,
        "size": f.size,
        "category": f.category,
        "accessRoles": list(f.access_roles),
        "linkedTo": linked,
        "encrypted": f.encrypted,
        "retentionUntil": f.retention_until,
        "createdAt": f.created_at,
    }


class MongoFileRepository(BaseMongoRepository[StoredFile], FileRepository):
    """FileRepository sobre la colección `files`."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._files = self._col

    def to_document(self, file: StoredFile) -> dict:
        """Archivo -> documento completo."""
        return _to_document(file)

    def to_entity(self, document: dict) -> StoredFile:
        """Documento -> archivo."""
        return _to_entity(document)

    def updates(self, file: StoredFile) -> dict:
        """Solo cambian el vínculo, los roles con acceso y la retención."""
        return {
            "accessRoles": list(file.access_roles),
            "linkedTo": (
                {"collection": file.linked_collection, "id": to_reference(file.linked_id)}
                if file.linked_collection and file.linked_id
                else None
            ),
            "retentionUntil": file.retention_until,
        }

    def list_by_owner(self, owner_id: str, *, limit: int = 50) -> list[StoredFile]:
        """Archivos del propietario, más recientes primero."""
        oid = to_object_id(owner_id)
        if oid is None:
            return []
        cursor = self._files.find({"ownerId": oid}).sort("createdAt", -1).limit(limit)
        return [_to_entity(doc) for doc in cursor]

    def list_by_link(self, collection: str, target_id: str) -> list[StoredFile]:
        """Archivos vinculados a un documento concreto."""
        oid = to_object_id(target_id)
        if oid is None:
            return []
        cursor = self._files.find({"linkedTo.collection": collection, "linkedTo.id": oid})
        return [_to_entity(doc) for doc in cursor]

    def list_expired(self, now: datetime, *, limit: int = 200) -> list[StoredFile]:
        """Archivos cuyo `retentionUntil` ya pasó (RN-06)."""
        cursor = self._files.find({"retentionUntil": {"$ne": None, "$lte": now}}).limit(limit)
        return [_to_entity(doc) for doc in cursor]
