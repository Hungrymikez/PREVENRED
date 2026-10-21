from abc import ABC, abstractmethod

from .aid import AidCategory, AidNeed, AidOffer, DonationMatch


class AidRepository(ABC):
    @abstractmethod
    async def save_offer(self, offer: AidOffer) -> None:
        pass

    @abstractmethod
    async def list_pending_offers(self, category: AidCategory | None = None) -> list[AidOffer]:
        pass

    @abstractmethod
    async def save_need(self, need: AidNeed) -> None:
        pass

    @abstractmethod
    async def list_pending_needs(self, category: AidCategory | None = None) -> list[AidNeed]:
        pass

    @abstractmethod
    async def save_match(self, match: DonationMatch) -> None:
        pass
