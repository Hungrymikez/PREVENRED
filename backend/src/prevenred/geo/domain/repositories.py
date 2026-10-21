from abc import ABC, abstractmethod

from .layer import LayerCategory, MapLayer


class GeoRepository(ABC):
    @abstractmethod
    async def save_layer(self, layer: MapLayer) -> None:
        pass

    @abstractmethod
    async def list_active_layers(self, category: LayerCategory | None = None) -> list[MapLayer]:
        pass
