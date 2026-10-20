import pytest

from prevenred.audit.application.record_audit import AuditUseCase, RecordAuditCommand
from prevenred.audit.domain.audit_log import AuditLog
from prevenred.audit.domain.repositories import AuditRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.shared.domain.errors import AuthorizationError, DomainValidationError


class InMemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self.logs: list[AuditLog] = []

    async def save(self, log: AuditLog) -> None:
        self.logs.append(log)

    async def list_recent(self, resource: str | None = None, limit: int = 100) -> list[AuditLog]:
        if resource:
            return [log for log in self.logs if log.resource == resource.lower()][:limit]
        return list(self.logs)[:limit]


@pytest.fixture
def admin_user() -> User:
    return User.register(
        email=Email("admin.audit@pereira.gov.co"),
        raw_password="AdminAuditPass2026*",
        name="Auditor General",
        role=Role.ADMIN,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def citizen_user() -> User:
    return User.register(
        email=Email("vecino@pereira.gov.co"),
        raw_password="CitizenPass2026*",
        name="Vecino",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_audit_logging_and_authorization(admin_user: User, citizen_user: User) -> None:
    repo = InMemoryAuditRepository()
    use_case = AuditUseCase(repo)

    # 1. Registrar evento
    log = await use_case.record_event(
        RecordAuditCommand(
            actor_id=admin_user.id.value,
            action="SWITCH_MODE",
            resource="operating_mode",
            resource_id="EMERGENCY",
            details={"reason": "Simulacro oficial DIGER"},
        )
    )
    assert log.action == "SWITCH_MODE"
    assert len(repo.logs) == 1

    # 2. Ciudadano no puede listar auditorías
    with pytest.raises(AuthorizationError):
        await use_case.list_logs(user=citizen_user)

    # 3. Admin sí puede listar
    results = await use_case.list_logs(user=admin_user)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_audit_domain_validations(admin_user: User) -> None:
    repo = InMemoryAuditRepository()
    use_case = AuditUseCase(repo)

    with pytest.raises(DomainValidationError, match="al menos 3 caracteres"):
        await use_case.record_event(
            RecordAuditCommand(
                actor_id=admin_user.id.value,
                action="NO",
                resource="incidents",
                resource_id="INC-1",
                details={},
            )
        )

    with pytest.raises(DomainValidationError, match="al menos 2 caracteres"):
        await use_case.record_event(
            RecordAuditCommand(
                actor_id=admin_user.id.value,
                action="CREATE",
                resource="",
                resource_id="INC-1",
                details={},
            )
        )
