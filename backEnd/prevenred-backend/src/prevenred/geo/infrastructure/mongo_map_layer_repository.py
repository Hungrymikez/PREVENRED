"""
Repositorio de capas del mapa sobre MongoDB: colección `map_layers` (CU-10, CU-40).

`visibleForRoles` guarda códigos de rol (texto), no ObjectId: el filtro de
visibilidad se resuelve con el rol que ya viene en el token (H-01 del doc 09).
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.geo.domain.map_layer import MapLayer
from prevenred.geo.domain.repositories import MapLayerRepository
from prevenred.shared.infrastructure.repository import BaseMongoRepository, utc_aware

COLLECTION = "map_layers"


def _to_entity(d: dict) -> MapLayer:
    """Documento -> MapLayer."""
    return MapLayer(
        id=str(d["_id"]),
        name=d["name"],
        type=d["type"],
        source=d.get("source", ""),
        geometry=d.get("geometry") or {},
        visible_for_roles=tuple(d.get("visibleForRoles") or ()),
        version=d.get("version", "1"),
        updated_at=utc_aware(d["updatedAt"]),
        created_at=utc_aware(d.get("createdAt") or d["updatedAt"]),
    )


def _to_document(layer: MapLayer) -> dict:
    """MapLayer -> documento completo."""
    return {
        "_id": ObjectId(layer.id),
        "name": layer.name,
        "type": layer.type,
        "source": layer.source,
        "geometry": layer.geometry,
        "visibleForRoles": list(layer.visible_for_roles),
        "version": layer.version,
        "updatedAt": layer.updated_at,
        "createdAt": layer.created_at,
    }


class MongoMapLayerRepository(BaseMongoRepository[MapLayer], MapLayerRepository):
    """MapLayerRepository sobre la colección `map_layers`."""
    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._layers = self._col

    def to_document(self, layer: MapLayer) -> dict:
        """Capa -> documento completo."""
        return _to_document(layer)

    def to_entity(self, document: dict) -> MapLayer:
        """Documento -> capa."""
        return _to_entity(document)

    def updates(self, layer: MapLayer) -> dict:
        """Cambian geometría, versión, fuente y visibilidad."""
        return {
            "geometry": layer.geometry,
            "source": layer.source,
            "version": layer.version,
            "visibleForRoles": list(layer.visible_for_roles),
            "updatedAt": layer.updated_at,
        }

    def get_by_name(self, name: str, version: str | None = None) -> MapLayer | None:
        """Busca por nombre y, opcionalmente, versión (la más reciente si se omite)."""
        query: dict = {"name": name}
        if version is not None:
            query["version"] = version
        doc = self._layers.find_one(query, sort=[("updatedAt", -1)])
        return _to_entity(doc) if doc else None

    def list_visible_for(self, role: str) -> list[MapLayer]:
        """Capas autorizadas para el rol, ordenadas por nombre."""
        cursor = self._layers.find({"visibleForRoles": role}).sort("name", 1)
        return [_to_entity(doc) for doc in cursor]
