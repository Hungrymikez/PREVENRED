from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .aid import AidCategory, AidNeed, AidOffer, DonationMatch


class AidRepository(ABC):
    @abstractmethod
    async def save_offer(self, offer: AidOffer) -> None:
        pass

    @abstractmethod
    async def list_pending_offers(self, category: AidCategory | None = None) -> list[AidOffer]:
        pass

    @abstractmethod
    async def list_offers_by_donor(self, donor_id: EntityId) -> list[AidOffer]:
        """CU-33: ofertas de un donante, más recientes primero."""

    @abstractmethod
    async def save_need(self, need: AidNeed) -> None:
        pass

    @abstractmethod
    async def list_pending_needs(self, category: AidCategory | None = None) -> list[AidNeed]:
        pass

    @abstractmethod
    async def save_match(self, match: DonationMatch) -> None:
        pass
