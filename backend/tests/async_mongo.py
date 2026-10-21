"""Adaptador asíncrono (estilo Motor) sobre mongomock para probar routers y repositorios Motor.

mongomock no implementa `$nearSphere`; aquí se emula con distancia haversine para poder
probar las búsquedas geoespaciales (radio, orden por cercanía) sin un MongoDB real.
"""

import math
from typing import Any

EARTH_RADIUS_METERS = 6371000.0


def haversine_meters(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AsyncCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = list(docs)

    def sort(self, key: str, direction: int = 1) -> "AsyncCursor":
        self._docs.sort(key=lambda d: d.get(key), reverse=direction < 0)
        return self

    def limit(self, n: int) -> "AsyncCursor":
        if n:
            self._docs = self._docs[:n]
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return self._docs[:length] if length else list(self._docs)


class AsyncCollection:
    def __init__(self, collection) -> None:
        self._col = collection

    async def find_one(self, *args, **kwargs):
        return self._col.find_one(*args, **kwargs)

    async def insert_one(self, *args, **kwargs):
        return self._col.insert_one(*args, **kwargs)

    async def replace_one(self, *args, **kwargs):
        return self._col.replace_one(*args, **kwargs)

    async def update_one(self, *args, **kwargs):
        return self._col.update_one(*args, **kwargs)

    async def count_documents(self, *args, **kwargs):
        return self._col.count_documents(*args, **kwargs)

    async def create_index(self, *args, **kwargs):
        return self._col.create_index(*args, **kwargs)

    def index_information(self) -> dict[str, Any]:
        return self._col.index_information()

    def aggregate(self, pipeline: list[dict[str, Any]]) -> AsyncCursor:
        return AsyncCursor(self._col.aggregate(pipeline))

    def find(self, filter: dict[str, Any] | None = None, *args, **kwargs) -> AsyncCursor:
        query = dict(filter or {})
        near = None
        for field, cond in list(query.items()):
            if isinstance(cond, dict) and "$nearSphere" in cond:
                near = (field, cond["$nearSphere"])
                del query[field]
        docs = list(self._col.find(query, *args, **kwargs))
        if near is None:
            return AsyncCursor(docs)

        field, spec = near
        lon, lat = spec["$geometry"]["coordinates"]
        max_distance = spec.get("$maxDistance", math.inf)
        scored = sorted(
            (haversine_meters(lon, lat, *doc[field]["coordinates"]), i, doc)
            for i, doc in enumerate(docs)
        )
        return AsyncCursor([doc for dist, _, doc in scored if dist <= max_distance])


class AsyncDatabase:
    def __init__(self, database) -> None:
        self._db = database

    def __getitem__(self, name: str) -> AsyncCollection:
        return AsyncCollection(self._db[name])
