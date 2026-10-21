import pytest

from prevenred.aid.application.manage_aid import (
    ExecuteMatchingCommand,
    ManageAidUseCase,
    OfferAidCommand,
    RequestAidCommand,
)
from prevenred.aid.domain.aid import (
    AidCategory,
    AidNeed,
    AidOffer,
    AidPriority,
    AidStatus,
    DonationMatch,
)
from prevenred.aid.domain.repositories import AidRepository
from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.shared.domain.errors import AuthorizationError, DomainValidationError


class InMemoryAidRepository(AidRepository):
    def __init__(self) -> None:
        self.offers: dict[str, AidOffer] = {}
        self.needs: dict[str, AidNeed] = {}
        self.matches: dict[str, DonationMatch] = {}

    async def save_offer(self, offer: AidOffer) -> None:
        self.offers[offer.id.value] = offer

    async def list_pending_offers(self, category=None) -> list[AidOffer]:
        return [o for o in self.offers.values() if o.status == AidStatus.PENDIENTE]

    async def save_need(self, need: AidNeed) -> None:
        self.needs[need.id.value] = need

    async def list_pending_needs(self, category=None) -> list[AidNeed]:
        return [n for n in self.needs.values() if n.status == AidStatus.PENDIENTE]

    async def save_match(self, match: DonationMatch) -> None:
        self.matches[match.id.value] = match


@pytest.fixture
def admin_user() -> User:
    return User.register(
        email=Email("admin.diger@pereira.gov.co"),
        raw_password="AdminPassword2026*",
        name="Coordinador DIGER",
        role=Role.ADMIN,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def citizen_user() -> User:
    return User.register(
        email=Email("vecino.afectado@pereira.gov.co"),
        raw_password="CitizenPass2026*",
        name="Vecino Afectado",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_aid_matching_algorithm(admin_user: User, citizen_user: User) -> None:
    repo = InMemoryAidRepository()
    use_case = ManageAidUseCase(repo)

    # 1. Registrar necesidad urgente
    await use_case.request_aid(
        RequestAidCommand(
            title="Agua potable urgente para 10 familias",
            category=AidCategory.AGUA,
            quantity=50.0,
            unit="litros",
            priority=AidPriority.URGENTE,
            longitude=-75.69,
            latitude=4.81,
            requester=citizen_user,
        )
    )

    # 2. Registrar donación disponible cercana
    await use_case.offer_aid(
        OfferAidCommand(
            title="Bidones de agua purificada",
            category=AidCategory.AGUA,
            quantity=60.0,
            unit="litros",
            longitude=-75.692,
            latitude=4.811,
            donor=citizen_user,
        )
    )

    # 3. Ejecutar algoritmo de matching
    matches = await use_case.run_matching(ExecuteMatchingCommand(admin_user=admin_user))

    assert len(matches) == 1
    m = matches[0]
    assert m.matched_quantity == 50.0
    assert m.distance_meters > 0
    assert len(repo.matches) == 1


@pytest.mark.asyncio
async def test_matching_requires_admin(citizen_user: User) -> None:
    repo = InMemoryAidRepository()
    use_case = ManageAidUseCase(repo)

    with pytest.raises(AuthorizationError, match="Solo administradores"):
        await use_case.run_matching(ExecuteMatchingCommand(admin_user=citizen_user))


@pytest.mark.asyncio
async def test_aid_domain_validations(citizen_user: User) -> None:
    repo = InMemoryAidRepository()
    use_case = ManageAidUseCase(repo)

    with pytest.raises(DomainValidationError, match="al menos 3 caracteres"):
        await use_case.request_aid(
            RequestAidCommand(
                title="no",
                category=AidCategory.ALIMENTOS,
                quantity=10.0,
                unit="kg",
                priority=AidPriority.MEDIA,
                longitude=-75.69,
                latitude=4.81,
                requester=citizen_user,
            )
        )

    with pytest.raises(DomainValidationError, match="mayor a 0"):
        await use_case.request_aid(
            RequestAidCommand(
                title="Alimentos no perecederos",
                category=AidCategory.ALIMENTOS,
                quantity=0.0,
                unit="kg",
                priority=AidPriority.MEDIA,
                longitude=-75.69,
                latitude=4.81,
                requester=citizen_user,
            )
        )

    with pytest.raises(DomainValidationError, match="Coordenadas geográficas inválidas"):
        await use_case.offer_aid(
            OfferAidCommand(
                title="Cobijas térmicas",
                category=AidCategory.REFUGIO,
                quantity=10.0,
                unit="unidades",
                longitude=-195.0,
                latitude=4.81,
                donor=citizen_user,
            )
        )


@pytest.mark.asyncio
async def test_matching_distance_cutoff(admin_user: User, citizen_user: User) -> None:
    repo = InMemoryAidRepository()
    use_case = ManageAidUseCase(repo)

    # Necesidad en Pereira
    await use_case.request_aid(
        RequestAidCommand(
            title="Herramientas para despeje",
            category=AidCategory.HERRAMIENTAS,
            quantity=5.0,
            unit="palas",
            priority=AidPriority.ALTA,
            longitude=-75.69,
            latitude=4.81,
            requester=citizen_user,
        )
    )

    # Donación lejana (Bogotá: lon=-74.08, lat=4.60, >150 km de distancia)
    await use_case.offer_aid(
        OfferAidCommand(
            title="Palas de construcción",
            category=AidCategory.HERRAMIENTAS,
            quantity=5.0,
            unit="palas",
            longitude=-74.08,
            latitude=4.60,
            donor=citizen_user,
        )
    )

    matches = await use_case.run_matching(
        ExecuteMatchingCommand(admin_user=admin_user, max_distance_meters=15000.0)
    )
    assert len(matches) == 0
