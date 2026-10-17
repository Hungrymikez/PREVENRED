"""Pruebas de APLICACIÓN de CU-08 (flujos A y E) con un directorio de cuentas falso."""
import pytest

from prevenred.identity.application.manage_users import (
    CREATABLE_ROLES,
    MFA_PURPOSE,
    ChangeRoleCommand,
    ChangeStatusCommand,
    CreateAccountCommand,
    ManageUsers,
)
from prevenred.identity.application.security import hash_one_time_code
from prevenred.identity.domain.mfa import LOGIN_PURPOSE, MfaChallenge
from prevenred.identity.domain.repositories import (
    RoleAssignmentAudit,
    SessionRevoker,
    UserDirectory,
)
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email, OneTimeCode, SecondFactorMethod
from prevenred.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.event_bus import InMemoryEventBus
from tests.identity.test_mfa_application import FakeChallenges


class FakeDirectory(UserDirectory):
    """Directorio de cuentas en memoria (cumple también LastAdminGuard)."""

    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    def get_by_id(self, user_id: str) -> User | None:
        return self.items.get(user_id)

    def get_by_email(self, email: Email) -> User | None:
        return next((u for u in self.items.values() if u.email.value == email.value), None)

    def add(self, user: User) -> None:
        self.items[user.id] = user

    def update(self, user: User) -> None:
        self.items[user.id] = user

    def list_by_role(self, role: str, *, limit: int = 100) -> list[User]:
        return [u for u in self.items.values() if u.role.value == role][:limit]

    def count_active_with_role(self, role: str) -> int:
        return sum(
            1 for u in self.items.values() if u.role.value == role and u.is_active
        )


class FakeSessions(SessionRevoker):
    """Registra las revocaciones en bloque (CU-08 A2)."""

    def __init__(self) -> None:
        self.revoked: list[str] = []

    def revoke_all(self, user_id: str) -> int:
        self.revoked.append(user_id)
        return 1


class FakeAudit(RoleAssignmentAudit):
    """Auditoría en memoria; puede simular que la base no responde (E3)."""

    def __init__(self, failing: bool = False) -> None:
        self.records: list[dict] = []
        self.failing = failing

    def record(self, *, actor_id: str, action: str, target_id: str, details: dict) -> None:
        if self.failing:
            raise ConflictError("No se pudo registrar la auditoría del cambio.")
        self.records.append(
            {"actor": actor_id, "action": action, "target": target_id, **details}
        )


class FakeHasher:
    """Hasher de apoyo: no necesita Argon2 para probar la orquestación."""

    def hash(self, plain: str) -> str:
        return f"hash::{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hash::{plain}"


def _account(directory, role=Role.CIUDADANO, email="x@mail.com", active=True, **extra):  # noqa: ANN001, ANN201
    """Cuenta YA existente: se rehidrata (register rechaza los roles internos)."""
    user = User.rehydrate(
        full_name="Persona Prueba", email=Email(email), password_hash="h", roles=(role,),
        neighborhood="Centro", privacy_notice_version="v1", terms_accepted_at=utcnow(),
        is_active=active, **extra,
    )
    directory.add(user)
    return user


def _verified(directory: FakeDirectory, purpose: str = MFA_PURPOSE):  # noqa: ANN201
    """Un Administrador con el segundo factor YA verificado para esa operación."""
    admin = _account(directory, role=Role.ADMINISTRADOR, email="admin@prevenred.gov.co")
    code = OneTimeCode("482913")
    challenge = MfaChallenge.open(
        user_id=admin.id, role=Role.ADMINISTRADOR, purpose=purpose,
        method=SecondFactorMethod("totp"), code_hash=hash_one_time_code(str(code)),
        secret_enc="enc:v1:a",
    )
    challenge.verify(code, code_matches=True)
    challenges = FakeChallenges()
    challenges.add(challenge)
    return admin, challenges


def _use_case(audit_log=None):  # noqa: ANN001, ANN201
    """Arma CU-08 con un Administrador ya verificado y devuelve todo lo observable."""
    directory = FakeDirectory()
    admin, challenges = _verified(directory)
    log = audit_log or FakeAudit()
    sessions = FakeSessions()
    use_case = ManageUsers(
        directory, challenges, FakeHasher(), sessions, log, InMemoryEventBus()
    )
    return use_case, directory, sessions, log, admin

# ---- A1: crear una cuenta de Inspector o de Administrador ----
def test_crea_inspector_con_contrasena_temporal():
    use_case, directory, _, log, admin = _use_case()

    result = use_case.create_account(CreateAccountCommand(
        actor_id=admin.id, full_name="Iván Inspector", email="ivan@prevenred.gov.co",
        role=Role.INSPECTOR, neighborhood="Cuba",
    ))

    assert result.user.role is Role.INSPECTOR
    assert result.user.is_active
    assert result.temporary_password and len(result.temporary_password) >= 8
    # Se guarda el HASH de la temporal, nunca la contraseña en claro.
    assert result.user.password_hash != result.temporary_password
    assert directory.get_by_id(result.user.id) is not None
    assert log.records == []      # la auditoría de CU-08 cubre cambios de rol/estado


def test_crea_administrador():
    use_case, _, _, _, admin = _use_case()
    result = use_case.create_account(CreateAccountCommand(
        actor_id=admin.id, full_name="Otro Admin", email="otro@prevenred.gov.co",
        role=Role.ADMINISTRADOR, neighborhood="Centro",
    ))
    assert result.user.role is Role.ADMINISTRADOR


def test_no_crea_roles_que_no_sean_administrativos():
    use_case, _, _, _, admin = _use_case()
    assert Role.CIUDADANO not in CREATABLE_ROLES
    with pytest.raises(ForbiddenError):
        use_case.create_account(CreateAccountCommand(
            actor_id=admin.id, full_name="Ciudadano", email="c@mail.com",
            role=Role.CIUDADANO, neighborhood="Cuba",
        ))


def test_no_duplica_correos():
    use_case, _, _, _, admin = _use_case()
    cmd = CreateAccountCommand(
        actor_id=admin.id, full_name="Iván Inspector", email="ivan@prevenred.gov.co",
        role=Role.INSPECTOR, neighborhood="Cuba",
    )
    use_case.create_account(cmd)
    with pytest.raises(ConflictError):
        use_case.create_account(cmd)


# ---- RN-07: sin verificación en dos pasos no se administra ----
def test_sin_segundo_factor_verificado_no_se_administra():
    directory = FakeDirectory()
    admin = _account(directory, role=Role.ADMINISTRADOR, email="a@prevenred.gov.co")
    use_case = ManageUsers(
        directory, FakeChallenges(), FakeHasher(), FakeSessions(), FakeAudit(),
        InMemoryEventBus(),
    )
    with pytest.raises(ForbiddenError):
        use_case.create_account(CreateAccountCommand(
            actor_id=admin.id, full_name="Iván Inspector", email="i@prevenred.gov.co",
            role=Role.INSPECTOR, neighborhood="Cuba",
        ))


def test_la_verificacion_del_login_no_sirve_para_administrar():
    """El MFA de CU-02 permite ENTRAR; no autoriza operaciones de administración."""
    directory = FakeDirectory()
    _, challenges = _verified(directory, purpose=LOGIN_PURPOSE)
    admin = next(u for u in directory.items.values())
    use_case = ManageUsers(
        directory, challenges, FakeHasher(), FakeSessions(), FakeAudit(),
        InMemoryEventBus(),
    )
    with pytest.raises(ForbiddenError):
        use_case.suspend(ChangeStatusCommand(actor_id=admin.id, user_id=admin.id))


def test_un_no_administrador_no_gestiona_usuarios():
    directory = FakeDirectory()
    inspector = _account(directory, role=Role.INSPECTOR, email="i@prevenred.gov.co")
    use_case = ManageUsers(
        directory, FakeChallenges(), FakeHasher(), FakeSessions(), FakeAudit(),
        InMemoryEventBus(),
    )
    with pytest.raises(ForbiddenError):
        use_case.suspend(ChangeStatusCommand(
            actor_id=inspector.id, user_id=inspector.id
        ))

# ---- A2: suspender (con revocación de sesiones) ----
def test_suspender_revoca_las_sesiones_y_audita():
    use_case, directory, sessions, log, admin = _use_case()
    target = _account(directory, email="tec@prevenred.gov.co", role=Role.TECNICO)

    result = use_case.suspend(ChangeStatusCommand(actor_id=admin.id, user_id=target.id))

    assert not result.user.is_active
    assert not directory.get_by_id(target.id).is_active
    assert sessions.revoked == [target.id]
    assert log.records[0]["action"] == "USER_SUSPENDED"


def test_suspender_una_cuenta_inexistente_informa_para_recargar():  # E2
    use_case, _, _, _, admin = _use_case()
    with pytest.raises(NotFoundError):
        use_case.suspend(ChangeStatusCommand(actor_id=admin.id, user_id="0" * 24))


def test_no_se_suspende_al_ultimo_administrador():  # E1
    directory = FakeDirectory()
    admin, challenges = _verified(directory)
    use_case = ManageUsers(
        directory, challenges, FakeHasher(), FakeSessions(), FakeAudit(),
        InMemoryEventBus(),
    )
    with pytest.raises(ConflictError):
        use_case.suspend(ChangeStatusCommand(actor_id=admin.id, user_id=admin.id))
    assert directory.get_by_id(admin.id).is_active


def test_reactivar_la_cuenta_la_deja_activa():
    use_case, directory, _, log, admin = _use_case()
    target = _account(directory, email="t@prevenred.gov.co", active=False)

    result = use_case.reactivate(ChangeStatusCommand(actor_id=admin.id, user_id=target.id))

    assert result.user.is_active
    assert log.records[0]["action"] == "USER_REACTIVATED"


# ---- paso 6: cambiar el rol ----
def test_asigna_rol_y_audita_el_cambio():
    use_case, directory, _, log, admin = _use_case()
    target = _account(directory, email="tec@prevenred.gov.co", role=Role.TECNICO)

    result = use_case.change_role(ChangeRoleCommand(
        actor_id=admin.id, user_id=target.id, role=Role.INSPECTOR,
        current_role=Role.TECNICO,
    ))

    assert result.user.role is Role.INSPECTOR
    assert directory.get_by_id(target.id).role is Role.INSPECTOR
    assert log.records[0]["previousRole"] == "TECNICO"
    assert log.records[0]["newRole"] == "INSPECTOR"


def test_si_otro_ya_cambio_el_rol_se_pide_recargar():  # E2
    use_case, directory, _, _, admin = _use_case()
    target = _account(directory, email="tec@prevenred.gov.co", role=Role.INSPECTOR)
    with pytest.raises(ConflictError):
        use_case.change_role(ChangeRoleCommand(
            actor_id=admin.id, user_id=target.id, role=Role.VOLUNTARIO,
            current_role=Role.TECNICO,     # lo que el administrador vio en pantalla
        ))


def test_un_administrador_no_puede_quitarse_su_propio_rol():  # E1
    directory = FakeDirectory()
    admin, challenges = _verified(directory)
    _account(directory, role=Role.ADMINISTRADOR, email="segundo@prevenred.gov.co")
    use_case = ManageUsers(
        directory, challenges, FakeHasher(), FakeSessions(), FakeAudit(),
        InMemoryEventBus(),
    )
    with pytest.raises(ForbiddenError):
        use_case.change_role(ChangeRoleCommand(
            actor_id=admin.id, user_id=admin.id, role=Role.INSPECTOR,
        ))


def test_cambiar_a_otro_administrador_activo_si_se_permite():  # E1 (positivo)
    directory = FakeDirectory()
    admin, challenges = _verified(directory)
    other = _account(directory, role=Role.ADMINISTRADOR, email="b@prevenred.gov.co")
    use_case = ManageUsers(
        directory, challenges, FakeHasher(), FakeSessions(), FakeAudit(),
        InMemoryEventBus(),
    )
    result = use_case.change_role(ChangeRoleCommand(
        actor_id=admin.id, user_id=other.id, role=Role.INSPECTOR,
        current_role=Role.ADMINISTRADOR,
    ))
    assert result.user.role is Role.INSPECTOR


# ---- E3: sin auditoría no hay cambio ----
def test_si_la_auditoria_falla_el_cambio_no_se_aplica():
    use_case, directory, sessions, _, admin = _use_case(audit_log=FakeAudit(failing=True))
    target = _account(directory, email="tec@prevenred.gov.co", role=Role.TECNICO)

    with pytest.raises(ConflictError):
        use_case.suspend(ChangeStatusCommand(actor_id=admin.id, user_id=target.id))

    assert directory.get_by_id(target.id).is_active       # no se suspendió
    assert sessions.revoked == []                          # ni se cerraron sesiones

