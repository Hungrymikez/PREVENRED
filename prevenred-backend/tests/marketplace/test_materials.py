import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.marketplace.application.publish_material import (
    PublishMaterialCommand,
    PublishMaterialUseCase,
)
from prevenred.marketplace.application.search_materials import (
    SearchMaterialsQuery,
    SearchMaterialsUseCase,
)
from prevenred.marketplace.domain.material import (
    Material,
    MaterialCategory,
    MaterialCondition,
    OfferType,
)
from prevenred.marketplace.domain.repositories import MaterialRepository
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


class InMemoryMaterialRepository(MaterialRepository):
    def __init__(self) -> None:
        self.items: dict[str, Material] = {}

    async def save(self, material: Material) -> None:
        self.items[material.id.value] = material

    async def get_by_id(self, material_id: EntityId) -> Material | None:
        return self.items.get(material_id.value)

    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 10000.0,
        category: MaterialCategory | None = None,
        offer_type: OfferType | None = None,
        limit: int = 50,
    ) -> list[Material]:
        res = list(self.items.values())
        if category:
            res = [m for m in res if m.category == category]
        if offer_type:
            res = [m for m in res if m.offer_type == offer_type]
        return res[:limit]


@pytest.fixture
def citizen_user() -> User:
    return User.register(
        email=Email("vecino.materiales@pereira.gov.co"),
        raw_password="SecurePass2026*",
        name="Don Jorge",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_publish_material_success(citizen_user: User) -> None:
    repo = InMemoryMaterialRepository()
    use_case = PublishMaterialUseCase(repo)

    cmd = PublishMaterialCommand(
        title="Ladrillos limpios sobrantes",
        description="Aproximadamente 200 ladrillos farol",
        category=MaterialCategory.CONSTRUCCION,
        offer_type=OfferType.DONACION,
        condition=MaterialCondition.BUENO,
        quantity=200,
        unit="unidades",
        longitude=-75.69,
        latitude=4.81,
        owner=citizen_user,
    )
    res = await use_case.execute(cmd)

    assert res.id is not None
    assert res.price == 0.0
    assert res.is_active is True
    assert len(repo.items) == 1


@pytest.mark.asyncio
async def test_publish_material_requires_price_on_sale(citizen_user: User) -> None:
    repo = InMemoryMaterialRepository()
    use_case = PublishMaterialUseCase(repo)

    with pytest.raises(DomainValidationError, match="se requiere un precio válido"):
        await use_case.execute(
            PublishMaterialCommand(
                title="Taladro percutor",
                description="Taladro industrial",
                category=MaterialCategory.HERRAMIENTAS,
                offer_type=OfferType.VENTA,
                condition=MaterialCondition.BUENO,
                quantity=1,
                unit="unidad",
                longitude=-75.69,
                latitude=4.81,
                owner=citizen_user,
                price=None,
            )
        )


@pytest.mark.asyncio
async def test_publish_material_rental_requires_valid_price(citizen_user: User) -> None:
    repo = InMemoryMaterialRepository()
    use_case = PublishMaterialUseCase(repo)

    with pytest.raises(DomainValidationError, match="se requiere un precio válido"):
        await use_case.execute(
            PublishMaterialCommand(
                title="Andamio tubular",
                description="Andamio de dos cuerpos",
                category=MaterialCategory.HERRAMIENTAS,
                offer_type=OfferType.ALQUILER,
                condition=MaterialCondition.BUENO,
                quantity=1,
                unit="juego",
                longitude=-75.69,
                latitude=4.81,
                owner=citizen_user,
                price=-10.0,
            )
        )


@pytest.mark.asyncio
async def test_publish_material_validations(citizen_user: User) -> None:
    repo = InMemoryMaterialRepository()
    use_case = PublishMaterialUseCase(repo)

    with pytest.raises(DomainValidationError, match="al menos 3 caracteres"):
        await use_case.execute(
            PublishMaterialCommand(
                title="ok",
                description="",
                category=MaterialCategory.MADERA,
                offer_type=OfferType.DONACION,
                condition=MaterialCondition.USADO,
                quantity=5,
                unit="tablas",
                longitude=-75.69,
                latitude=4.81,
                owner=citizen_user,
            )
        )

    with pytest.raises(DomainValidationError, match="mayor a 0"):
        await use_case.execute(
            PublishMaterialCommand(
                title="Tablas de pino",
                description="",
                category=MaterialCategory.MADERA,
                offer_type=OfferType.DONACION,
                condition=MaterialCondition.USADO,
                quantity=0,
                unit="tablas",
                longitude=-75.69,
                latitude=4.81,
                owner=citizen_user,
            )
        )

    with pytest.raises(DomainValidationError, match="Coordenadas"):
        await use_case.execute(
            PublishMaterialCommand(
                title="Tablas de pino",
                description="",
                category=MaterialCategory.MADERA,
                offer_type=OfferType.DONACION,
                condition=MaterialCondition.USADO,
                quantity=2,
                unit="tablas",
                longitude=-200.0,
                latitude=4.81,
                owner=citizen_user,
            )
        )


@pytest.mark.asyncio
async def test_search_materials(citizen_user: User) -> None:
    repo = InMemoryMaterialRepository()
    publish_uc = PublishMaterialUseCase(repo)
    search_uc = SearchMaterialsUseCase(repo)

    await publish_uc.execute(
        PublishMaterialCommand(
            title="Madera pino",
            description="",
            category=MaterialCategory.MADERA,
            offer_type=OfferType.DONACION,
            condition=MaterialCondition.BUENO,
            quantity=10,
            unit="tablas",
            longitude=-75.69,
            latitude=4.81,
            owner=citizen_user,
        )
    )
    await publish_uc.execute(
        PublishMaterialCommand(
            title="Tubería PVC",
            description="",
            category=MaterialCategory.PLOMERIA,
            offer_type=OfferType.VENTA,
            condition=MaterialCondition.NUEVO,
            quantity=5,
            unit="tubos",
            longitude=-75.69,
            latitude=4.81,
            owner=citizen_user,
            price=25000.0,
        )
    )

    all_items = await search_uc.execute(SearchMaterialsQuery(longitude=-75.69, latitude=4.81))
    assert len(all_items) == 2

    plomeria = await search_uc.execute(
        SearchMaterialsQuery(
            longitude=-75.69,
            latitude=4.81,
            category=MaterialCategory.PLOMERIA,
        )
    )
    assert len(plomeria) == 1
    assert plomeria[0].category == MaterialCategory.PLOMERIA

    donaciones = await search_uc.execute(
        SearchMaterialsQuery(
            longitude=-75.69,
            latitude=4.81,
            offer_type=OfferType.DONACION,
        )
    )
    assert len(donaciones) == 1
    assert donaciones[0].offer_type == OfferType.DONACION
