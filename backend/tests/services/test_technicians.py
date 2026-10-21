import pytest

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.services.application.manage_technician import (
    RegisterTechnicianProfileCommand,
    RegisterTechnicianProfileUseCase,
    VerifyTechnicianCommand,
    VerifyTechnicianUseCase,
)
from prevenred.services.domain.repositories import TechnicianRepository
from prevenred.services.domain.technician import (
    Specialty,
    TechnicianProfile,
    VerificationStatus,
)
from prevenred.shared.domain.errors import AuthorizationError, DomainValidationError, NotFoundError
from prevenred.shared.domain.ids import EntityId


class InMemoryTechnicianRepository(TechnicianRepository):
    def __init__(self) -> None:
        self.items: dict[str, TechnicianProfile] = {}

    async def save(self, profile: TechnicianProfile) -> None:
        self.items[profile.id.value] = profile

    async def get_by_id(self, profile_id: EntityId) -> TechnicianProfile | None:
        return self.items.get(profile_id.value)

    async def get_by_user_id(self, user_id: EntityId) -> TechnicianProfile | None:
        for p in self.items.values():
            if p.user_id == user_id:
                return p
        return None

    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 15000.0,
        specialty: Specialty | None = None,
        only_verified: bool = True,
        limit: int = 50,
    ) -> list[TechnicianProfile]:
        res = list(self.items.values())
        if only_verified:
            res = [p for p in res if p.verification_status == VerificationStatus.VERIFIED]
        if specialty:
            res = [p for p in res if specialty in p.specialties]
        return res[:limit]


@pytest.fixture
def tech_user() -> User:
    return User.register(
        email=Email("maestro.plomero@pereira.gov.co"),
        raw_password="TechPass2026*",
        name="Maestro Roberto",
        role=Role.TECNICO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def admin_user() -> User:
    return User.register(
        email=Email("admin.diger@pereira.gov.co"),
        raw_password="AdminPass2026*",
        name="Admin DIGER",
        role=Role.ADMIN,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_register_and_verify_technician(tech_user: User, admin_user: User) -> None:
    repo = InMemoryTechnicianRepository()
    use_case_reg = RegisterTechnicianProfileUseCase(repo)

    cmd_reg = RegisterTechnicianProfileCommand(
        full_name="Roberto Gomez",
        phone_number="+573101234567",
        specialties=[Specialty.PLOMERIA, Specialty.CONSTRUCCION],
        experience_years=12,
        bio="Experto en tuberias y reparaciones sanitarias",
        longitude=-75.69,
        latitude=4.81,
        user=tech_user,
    )
    profile = await use_case_reg.execute(cmd_reg)

    assert profile.verification_status == VerificationStatus.PENDING
    assert "https://wa.me/573101234567" in profile.generate_whatsapp_link()

    use_case_ver = VerifyTechnicianUseCase(repo)
    verified = await use_case_ver.execute(
        VerifyTechnicianCommand(
            technician_id=profile.id.value,
            approve=True,
            admin_user=admin_user,
        )
    )
    assert verified.verification_status == VerificationStatus.VERIFIED
    assert verified.verified_by == EntityId(admin_user.id.value)


@pytest.mark.asyncio
async def test_verify_technician_forbidden_for_non_admin(tech_user: User) -> None:
    repo = InMemoryTechnicianRepository()
    use_case_ver = VerifyTechnicianUseCase(repo)

    with pytest.raises(AuthorizationError):
        await use_case_ver.execute(
            VerifyTechnicianCommand(
                technician_id="non-existent",
                approve=True,
                admin_user=tech_user,
            )
        )


@pytest.mark.asyncio
async def test_verify_technician_not_found(admin_user: User) -> None:
    repo = InMemoryTechnicianRepository()
    use_case_ver = VerifyTechnicianUseCase(repo)

    with pytest.raises(NotFoundError):
        await use_case_ver.execute(
            VerifyTechnicianCommand(
                technician_id="missing-id",
                approve=True,
                admin_user=admin_user,
            )
        )


@pytest.mark.asyncio
async def test_register_technician_update_existing(tech_user: User) -> None:
    repo = InMemoryTechnicianRepository()
    use_case_reg = RegisterTechnicianProfileUseCase(repo)

    cmd1 = RegisterTechnicianProfileCommand(
        full_name="Roberto Gomez",
        phone_number="+573101234567",
        specialties=[Specialty.PLOMERIA],
        experience_years=10,
        bio="Plomero",
        longitude=-75.69,
        latitude=4.81,
        user=tech_user,
    )
    p1 = await use_case_reg.execute(cmd1)

    cmd2 = RegisterTechnicianProfileCommand(
        full_name="Roberto Gomez Updated",
        phone_number="+573109876543",
        specialties=[Specialty.PLOMERIA, Specialty.ELECTRICIDAD],
        experience_years=11,
        bio="Plomero y electricista",
        longitude=-75.69,
        latitude=4.81,
        user=tech_user,
    )
    p2 = await use_case_reg.execute(cmd2)

    assert p2.id == p1.id
    assert p2.full_name == "Roberto Gomez Updated"
    assert p2.experience_years == 11
    assert len(repo.items) == 1


@pytest.mark.asyncio
async def test_technician_validations(tech_user: User) -> None:
    repo = InMemoryTechnicianRepository()
    use_case_reg = RegisterTechnicianProfileUseCase(repo)

    with pytest.raises(DomainValidationError, match="al menos 3 caracteres"):
        await use_case_reg.execute(
            RegisterTechnicianProfileCommand(
                full_name="Ro",
                phone_number="+573101234567",
                specialties=[Specialty.PLOMERIA],
                experience_years=1,
                bio="",
                longitude=-75.69,
                latitude=4.81,
                user=tech_user,
            )
        )

    with pytest.raises(DomainValidationError, match="inválido"):
        await use_case_reg.execute(
            RegisterTechnicianProfileCommand(
                full_name="Roberto Gomez",
                phone_number="123",
                specialties=[Specialty.PLOMERIA],
                experience_years=1,
                bio="",
                longitude=-75.69,
                latitude=4.81,
                user=tech_user,
            )
        )

    with pytest.raises(DomainValidationError, match="al menos una especialidad"):
        await use_case_reg.execute(
            RegisterTechnicianProfileCommand(
                full_name="Roberto Gomez",
                phone_number="+573101234567",
                specialties=[],
                experience_years=1,
                bio="",
                longitude=-75.69,
                latitude=4.81,
                user=tech_user,
            )
        )

    with pytest.raises(DomainValidationError, match="negativos"):
        await use_case_reg.execute(
            RegisterTechnicianProfileCommand(
                full_name="Roberto Gomez",
                phone_number="+573101234567",
                specialties=[Specialty.PLOMERIA],
                experience_years=-1,
                bio="",
                longitude=-75.69,
                latitude=4.81,
                user=tech_user,
            )
        )


@pytest.mark.asyncio
async def test_whatsapp_link_generation(tech_user: User) -> None:
    repo = InMemoryTechnicianRepository()
    use_case_reg = RegisterTechnicianProfileUseCase(repo)

    profile = await use_case_reg.execute(
        RegisterTechnicianProfileCommand(
            full_name="Roberto Gomez",
            phone_number="+573101234567",
            specialties=[Specialty.CARPINTERIA],
            experience_years=5,
            bio="Carpintería fina",
            longitude=-75.69,
            latitude=4.81,
            user=tech_user,
        )
    )
    custom_link = profile.generate_whatsapp_link(message="Cotización puerta")
    assert "https://wa.me/573101234567" in custom_link
    assert "Cotizaci%C3%B3n%20puerta" in custom_link
