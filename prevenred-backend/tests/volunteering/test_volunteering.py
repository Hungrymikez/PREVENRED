import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.shared.domain.errors import (
    AuthorizationError,
    DomainValidationError,
    NotFoundError,
)
from prevenred.shared.domain.ids import EntityId
from prevenred.volunteering.application.manage_volunteering import (
    AssignVolunteerCommand,
    ManageVolunteeringUseCase,
    RegisterVolunteerCommand,
)
from prevenred.volunteering.domain.repositories import VolunteerRepository
from prevenred.volunteering.domain.volunteer import (
    AssignmentStatus,
    VolunteerAssignment,
    VolunteerProfile,
    VolunteerSkill,
)


class InMemoryVolunteerRepository(VolunteerRepository):
    def __init__(self) -> None:
        self.profiles: dict[str, VolunteerProfile] = {}
        self.assignments: dict[str, VolunteerAssignment] = {}

    async def save_profile(self, profile: VolunteerProfile) -> None:
        self.profiles[profile.id.value] = profile

    async def get_by_user_id(self, user_id: EntityId) -> VolunteerProfile | None:
        for p in self.profiles.values():
            if p.user_id == user_id:
                return p
        return None

    async def get_by_id(self, volunteer_id: EntityId) -> VolunteerProfile | None:
        return self.profiles.get(volunteer_id.value)

    async def save_assignment(self, assignment: VolunteerAssignment) -> None:
        self.assignments[assignment.id.value] = assignment

    async def list_assignments_by_volunteer(
        self, volunteer_id: EntityId
    ) -> list[VolunteerAssignment]:
        return [a for a in self.assignments.values() if a.volunteer_id == volunteer_id]


@pytest.fixture
def volunteer_user() -> User:
    return User.register(
        email=Email("voluntario.rescatista@pereira.gov.co"),
        raw_password="VolPass2026*",
        name="Rescatista Mateo",
        role=Role.VOLUNTARIO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def inspector_user() -> User:
    return User.register(
        email=Email("coordinador.campo@diger.gov.co"),
        raw_password="CoordPass2026*",
        name="Coordinador DIGER",
        role=Role.INSPECTOR,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_register_and_assign_volunteer(volunteer_user: User, inspector_user: User) -> None:
    repo = InMemoryVolunteerRepository()
    use_case = ManageVolunteeringUseCase(repo)

    # Registro voluntario
    vol = await use_case.register_volunteer(
        RegisterVolunteerCommand(
            full_name="Mateo Morales",
            phone_number="+573123456789",
            skills=[VolunteerSkill.PRIMEROS_AUXILIOS, VolunteerSkill.RESCATE],
            longitude=-75.69,
            latitude=4.81,
            user=volunteer_user,
        )
    )
    assert vol.id is not None
    assert vol.is_available is True

    # Asignación a tarea de campo
    assignment = await use_case.assign_volunteer(
        AssignVolunteerCommand(
            volunteer_id=vol.id.value,
            incident_id="INC-20261016-A1B2C3",
            task_description="Apoyo en primeros auxilios en carpa de evacuación",
            coordinator=inspector_user,
        )
    )
    assert assignment.status == AssignmentStatus.ASIGNADO
    assert len(repo.assignments) == 1


@pytest.mark.asyncio
async def test_assign_volunteer_requires_coordinator(
    volunteer_user: User,
) -> None:
    repo = InMemoryVolunteerRepository()
    use_case = ManageVolunteeringUseCase(repo)

    with pytest.raises(AuthorizationError, match="Solo coordinadores"):
        await use_case.assign_volunteer(
            AssignVolunteerCommand(
                volunteer_id="any-vol-id",
                incident_id="INC-001",
                task_description="Tarea de inspección",
                coordinator=volunteer_user,
            )
        )


@pytest.mark.asyncio
async def test_assign_volunteer_not_found(inspector_user: User) -> None:
    repo = InMemoryVolunteerRepository()
    use_case = ManageVolunteeringUseCase(repo)

    with pytest.raises(NotFoundError, match="no encontrado"):
        await use_case.assign_volunteer(
            AssignVolunteerCommand(
                volunteer_id="non-existent-vol",
                incident_id="INC-001",
                task_description="Tarea de rescate y traslado",
                coordinator=inspector_user,
            )
        )


@pytest.mark.asyncio
async def test_update_existing_volunteer_profile(volunteer_user: User) -> None:
    repo = InMemoryVolunteerRepository()
    use_case = ManageVolunteeringUseCase(repo)

    vol1 = await use_case.register_volunteer(
        RegisterVolunteerCommand(
            full_name="Mateo Morales",
            phone_number="+573123456789",
            skills=[VolunteerSkill.PRIMEROS_AUXILIOS],
            longitude=-75.69,
            latitude=4.81,
            user=volunteer_user,
        )
    )

    # Actualizar perfil
    vol2 = await use_case.register_volunteer(
        RegisterVolunteerCommand(
            full_name="Mateo Morales Cruz",
            phone_number="+573009876543",
            skills=[VolunteerSkill.PRIMEROS_AUXILIOS, VolunteerSkill.LOGISTICA],
            longitude=-75.70,
            latitude=4.82,
            user=volunteer_user,
        )
    )

    assert vol1.id == vol2.id
    assert vol2.full_name == "Mateo Morales Cruz"
    assert vol2.phone_number == "+573009876543"
    assert len(vol2.skills) == 2
    assert len(repo.profiles) == 1


@pytest.mark.asyncio
async def test_volunteer_domain_validations(volunteer_user: User) -> None:
    repo = InMemoryVolunteerRepository()
    use_case = ManageVolunteeringUseCase(repo)

    with pytest.raises(DomainValidationError, match="al menos 3 caracteres"):
        await use_case.register_volunteer(
            RegisterVolunteerCommand(
                full_name="Ab",
                phone_number="+573123456789",
                skills=[VolunteerSkill.CONDUCCION],
                longitude=-75.69,
                latitude=4.81,
                user=volunteer_user,
            )
        )

    with pytest.raises(DomainValidationError, match="al menos una habilidad"):
        await use_case.register_volunteer(
            RegisterVolunteerCommand(
                full_name="Mateo Morales",
                phone_number="+573123456789",
                skills=[],
                longitude=-75.69,
                latitude=4.81,
                user=volunteer_user,
            )
        )

    with pytest.raises(DomainValidationError, match="Coordenadas geográficas inválidas"):
        await use_case.register_volunteer(
            RegisterVolunteerCommand(
                full_name="Mateo Morales",
                phone_number="+573123456789",
                skills=[VolunteerSkill.RESCATE],
                longitude=-75.69,
                latitude=-95.0,
                user=volunteer_user,
            )
        )
