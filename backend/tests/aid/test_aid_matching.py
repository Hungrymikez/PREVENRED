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

    async def list_offers_by_donor(self, donor_id) -> list[AidOffer]:
        return [o for o in self.offers.values() if o.donor_id == donor_id]

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


@pytest.mark.asyncio
async def test_matching_parcial_conserva_el_sobrante(admin_user: User, citizen_user: User) -> None:
    """CU-42: emparejar 50 de 60 litros deja 10 disponibles en la oferta (no se pierden)."""
    repo = InMemoryAidRepository()
    use_case = ManageAidUseCase(repo)
    need = await use_case.request_aid(
        RequestAidCommand(
            title="Agua para albergue",
            category=AidCategory.AGUA,
            quantity=50.0,
            unit="litros",
            priority=AidPriority.ALTA,
            longitude=-75.69,
            latitude=4.81,
            requester=citizen_user,
        )
    )
    offer = await use_case.offer_aid(
        OfferAidCommand(
            title="Agua embotellada",
            category=AidCategory.AGUA,
            quantity=60.0,
            unit="litros",
            longitude=-75.691,
            latitude=4.811,
            donor=citizen_user,
        )
    )

    [match] = await use_case.run_matching(ExecuteMatchingCommand(admin_user=admin_user))

    assert match.matched_quantity == 50.0
    assert need.status == AidStatus.EMPAREJADO and need.remaining_quantity == 0
    assert offer.status == AidStatus.PENDIENTE
    assert offer.available_quantity == pytest.approx(10.0)
    assert offer.quantity == 60.0  # la cantidad original se conserva

    # Una nueva necesidad usa el sobrante de la misma oferta
    otra = await use_case.request_aid(
        RequestAidCommand(
            title="Agua para comedor",
            category=AidCategory.AGUA,
            quantity=30.0,
            unit="litros",
            priority=AidPriority.MEDIA,
            longitude=-75.69,
            latitude=4.81,
            requester=citizen_user,
        )
    )
    [segundo] = await use_case.run_matching(ExecuteMatchingCommand(admin_user=admin_user))
    assert segundo.offer_id == offer.id
    assert segundo.matched_quantity == pytest.approx(10.0)
    assert offer.status == AidStatus.EMPAREJADO
    assert otra.status == AidStatus.PENDIENTE
    assert otra.remaining_quantity == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_una_necesidad_se_cubre_con_varias_ofertas(
    admin_user: User, citizen_user: User
) -> None:
    repo = InMemoryAidRepository()
    use_case = ManageAidUseCase(repo)
    need = await use_case.request_aid(
        RequestAidCommand(
            title="Mercados familiares",
            category=AidCategory.ALIMENTOS,
            quantity=10.0,
            unit="kg",
            priority=AidPriority.URGENTE,
            longitude=-75.69,
            latitude=4.81,
            requester=citizen_user,
        )
    )
    for qty in (4.0, 4.0):
        await use_case.offer_aid(
            OfferAidCommand(
                title="Arroz",
                category=AidCategory.ALIMENTOS,
                quantity=qty,
                unit="kg",
                longitude=-75.69,
                latitude=4.81,
                donor=citizen_user,
            )
        )
    matches = await use_case.run_matching(ExecuteMatchingCommand(admin_user=admin_user))
    assert [m.matched_quantity for m in matches] == [4.0, 4.0]
    assert need.status == AidStatus.PENDIENTE
    assert need.remaining_quantity == pytest.approx(2.0)
