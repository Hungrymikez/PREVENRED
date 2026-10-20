"""Puerto de persistencia de capas del mapa (CU-10, CU-40)."""
from abc import ABC, abstractmethod

from prevenred.geo.domain.map_layer import MapLayer


class MapLayerRepository(ABC):
    """Puerto de las capas geográficas autorizadas."""

    @abstractmethod
    def get_by_id(self, layer_id: str) -> MapLayer | None:
        """Busca una capa por id; None si no existe."""

    @abstractmethod
    def get_by_name(self, name: str, version: str | None = None) -> MapLayer | None:
        """Busca por nombre (y versión, si se indica)."""

    @abstractmethod
    def add(self, layer: MapLayer) -> None:
        """Publica una capa nueva."""

    @abstractmethod
    def update(self, layer: MapLayer) -> None:
        """Guarda una versión nueva o un cambio de visibilidad."""

    @abstractmethod
    def list_visible_for(self, role: str) -> list[MapLayer]:
        """Capas que ese rol puede cargar (CU-10)."""
