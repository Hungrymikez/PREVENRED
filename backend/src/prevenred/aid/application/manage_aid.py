import math
from dataclasses import dataclass

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.shared.domain.errors import AuthorizationError
from prevenred.shared.domain.ids import EntityId

from ..domain.aid import (
    AidCategory,
    AidNeed,
    AidOffer,
    AidPriority,
    AidStatus,
    DonationMatch,
)
from ..domain.repositories import AidRepository


def _calculate_haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


@dataclass(frozen=True)
class RequestAidCommand:
    title: str
    category: AidCategory
    quantity: float
    unit: str
    priority: AidPriority
    longitude: float
    latitude: float
    requester: User


@dataclass(frozen=True)
class OfferAidCommand:
    title: str
    category: AidCategory
    quantity: float
    unit: str
    longitude: float
    latitude: float
    donor: User
    source_material_id: str | None = None


@dataclass(frozen=True)
class ExecuteMatchingCommand:
    admin_user: User
    max_distance_meters: float = 15000.0


class ManageAidUseCase:
    def __init__(self, repository: AidRepository) -> None:
        self._repository = repository

    async def request_aid(self, command: RequestAidCommand) -> AidNeed:
        requester_id = EntityId(command.requester.id)
        need = AidNeed.create(
            title=command.title,
            category=command.category,
            quantity=command.quantity,
            unit=command.unit,
            priority=command.priority,
            requester_id=requester_id,
            longitude=command.longitude,
            latitude=command.latitude,
        )
        await self._repository.save_need(need)
        return need

    async def offer_aid(self, command: OfferAidCommand) -> AidOffer:
        source_id = EntityId(command.source_material_id) if command.source_material_id else None
        donor_id = EntityId(command.donor.id)
        offer = AidOffer.create(
            title=command.title,
            category=command.category,
            quantity=command.quantity,
            unit=command.unit,
            donor_id=donor_id,
            longitude=command.longitude,
            latitude=command.latitude,
            source_material_id=source_id,
        )
        await self._repository.save_offer(offer)
        return offer

    async def run_matching(self, command: ExecuteMatchingCommand) -> list[DonationMatch]:
        if command.admin_user.role != Role.ADMIN:
            raise AuthorizationError("Solo administradores pueden ejecutar el matching de ayudas.")

        needs = await self._repository.list_pending_needs()
        offers = await self._repository.list_pending_offers()

        matches_created: list[DonationMatch] = []

        # Ponderación por prioridad: URGENTE > ALTA > MEDIA > BAJA
        priority_order = {
            AidPriority.URGENTE: 0,
            AidPriority.ALTA: 1,
            AidPriority.MEDIA: 2,
            AidPriority.BAJA: 3,
        }
        sorted_needs = sorted(needs, key=lambda n: priority_order.get(n.priority, 4))

        for need in sorted_needs:
            compatible_offers = [
                o
                for o in offers
                if o.status == AidStatus.PENDIENTE
                and o.category == need.category
                and o.unit == need.unit
            ]

            if not compatible_offers:
                continue

            # Buscar la oferta más cercana geográficamente
            best_offer = None
            min_dist = float("inf")
            for off in compatible_offers:
                dist = _calculate_haversine(
                    need.longitude, need.latitude, off.longitude, off.latitude
                )
                if dist <= command.max_distance_meters and dist < min_dist:
                    min_dist = dist
                    best_offer = off

            if best_offer:
                matched_qty = min(need.quantity, best_offer.quantity)
                admin_id = EntityId(command.admin_user.id)
                match = DonationMatch.create(
                    need_id=need.id,
                    offer_id=best_offer.id,
                    matched_quantity=matched_qty,
                    distance_meters=round(min_dist, 2),
                    matched_by=admin_id,
                )
                await self._repository.save_match(match)

                need.status = AidStatus.EMPAREJADO
                best_offer.status = AidStatus.EMPAREJADO
                await self._repository.save_need(need)
                await self._repository.save_offer(best_offer)

                matches_created.append(match)

        return matches_created
