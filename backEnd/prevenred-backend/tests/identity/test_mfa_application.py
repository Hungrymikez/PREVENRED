"""Pruebas de APLICACIÓN de CU-03 (flujos A y E) con repositorios en memoria."""
import pytest

from prevenred.identity.application.reset_mfa import (
    ResetMfaOnServiceUnavailable,
    ServiceUnavailableCommand,
)
from prevenred.identity.application.security import hash_one_time_code
from prevenred.identity.application.validate_mfa import (
    RequestMfaCode,
    RequestMfaCommand,
    VerifyMfaCode,
    VerifyMfaCommand,
)
from prevenred.identity.domain.events import (
    MfaVerificationFailed,
    MfaVerificationLocked,
)
from prevenred.identity.domain.mfa import MFA_MAX_ATTEMPTS, MfaChallenge
from prevenred.identity.domain.repositories import MfaChallengeRepository, UserRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.second_factor_gateway import (
    InMemorySecondFactorGateway,
)
from prevenred.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    TooManyAttemptsError,
    UnauthorizedError,
)
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.event_bus import InMemoryEventBus

_PURPOSE = "cambio_de_modo"


# ---- Dobles de prueba: solo lo que estos casos de uso usan ----
class FakeUsers(UserRepository):
    """Guarda las cuentas en un diccionario."""

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


class FakeChallenges(MfaChallengeRepository):
    """Desafíos en memoria, con las dos consultas que usan los casos de uso."""

    def __init__(self) -> None:
        self.items: dict[str, MfaChallenge] = {}

    def add(self, challenge: MfaChallenge) -> None:
        self.items[challenge.id] = challenge

    def get_by_id(self, challenge_id: str) -> MfaChallenge | None:
        return self.items.get(challenge_id)

    def get_pending_by_user(self, user_id: str, purpose: str) -> MfaChallenge | None:
        pending = [
            c for c in self.items.values()
            if c.user_id == user_id and c.purpose == purpose and c.status == "PENDIENTE"
        ]
        return max(pending, key=lambda c: c.created_at, default=None)

    def get_latest_verified(self, user_id, purpose, *, since):  # noqa: ANN001, ANN201
        verified = [
            c for c in self.items.values()
            if c.user_id == user_id and c.purpose == purpose
            and c.status == "VERIFICADO" and c.verified_at is not None
            and c.verified_at >= since
        ]
        return max(verified, key=lambda c: c.verified_at, default=None)

    def get_blocked_by_user(self, user_id, purpose, *, since):  # noqa: ANN001, ANN201
        blocked = [
            c for c in self.items.values()
            if c.user_id == user_id and c.purpose == purpose
            and c.status == "BLOQUEADO" and c.created_at >= since
        ]
        return max(blocked, key=lambda c: c.created_at, default=None)

    def update(self, challenge: MfaChallenge) -> None:
        self.items[challenge.id] = challenge

    def expire_stale(self, user_id: str) -> None:
        now = utcnow()
        for challenge in self.items.values():
            if challenge.user_id == user_id and challenge.status == "PENDIENTE":
                if challenge.is_expired(now):
                    challenge.status = "EXPIRADO"


def _admin(users: FakeUsers, role: Role = Role.ADMINISTRADOR) -> User:
    """Cuenta administrativa YA existente (la creó un Administrador, CU-08)."""
    user = User.rehydrate(
        full_name="Ana Admin", email=Email("ana@prevenred.gov.co"), password_hash="h",
        roles=(role,), neighborhood="Centro", privacy_notice_version="v1",
        terms_accepted_at=utcnow(), mfa_enabled=True, mfa_secret_enc="enc:v1:ana",
    )
    users.add(user)
    return user


def _use_cases(users=None, challenges=None, gateway=None, events=None):  # noqa: ANN001
    users = users or FakeUsers()
    challenges = challenges or FakeChallenges()
    gateway = gateway or InMemorySecondFactorGateway()
    events = events or InMemoryEventBus()
    return (
        RequestMfaCode(users, challenges, gateway, events),
        VerifyMfaCode(users, challenges, gateway, events),
        users, challenges, events,
    )


# ---- Flujo A: pedir el código ----
def test_pide_codigo_y_abre_el_desafio():
    request, _, users, challenges, _ = _use_cases()
    admin = _admin(users)

    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))

    assert len(view.code.value) == 6 and view.code.value.isdigit()
    assert challenges.items[view.challenge_id].status == "PENDIENTE"
    # El código NUNCA se guarda en claro: solo su hash.
    stored = challenges.items[view.challenge_id]
    assert stored.code_hash == hash_one_time_code(str(view.code))
    assert view.code.value != stored.code_hash


def test_codigo_vigente_no_deja_abrir_otro():
    request, _, users, _, _ = _use_cases()
    admin = _admin(users)
    request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))
    with pytest.raises(ConflictError):
        request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))


def test_solo_las_cuentas_administrativas_piden_codigo():
    request, _, users, _, _ = _use_cases()
    inspector = _admin(users, role=Role.INSPECTOR)
    with pytest.raises(ForbiddenError):
        request.execute(RequestMfaCommand(user_id=inspector.id, purpose=_PURPOSE))


def test_el_secreto_queda_cifrado_en_la_cuenta():
    request, _, users, _, _ = _use_cases()
    admin = _admin(users)

    request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))

    stored = users.get_by_id(admin.id)
    assert stored.mfa_enabled and stored.mfa_secret_enc.startswith("enc:v1:")


# ---- Flujo A: validar el código ----
def test_codigo_correcto_satisface_la_operacion():
    request, verify, users, challenges, _ = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))

    result = verify.execute(
        VerifyMfaCommand(user_id=admin.id, purpose=_PURPOSE, code=str(view.code))
    )

    assert result.is_satisfied
    assert challenges.items[view.challenge_id].verified_at is not None


def test_codigo_incorrecto_no_autoriza_y_cuenta_el_intento():
    request, verify, users, challenges, events = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))
    fallos = []
    events.subscribe(MfaVerificationFailed, fallos.append)

    with pytest.raises(UnauthorizedError):
        verify.execute(VerifyMfaCommand(user_id=admin.id, purpose=_PURPOSE, code="000000"))

    assert challenges.items[view.challenge_id].attempts == 1
    assert challenges.items[view.challenge_id].status == "PENDIENTE"
    assert len(fallos) == 1


def test_texto_mal_formado_cuenta_como_intento_fallido():
    request, verify, users, challenges, _ = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))

    with pytest.raises(UnauthorizedError):
        verify.execute(VerifyMfaCommand(user_id=admin.id, purpose=_PURPOSE, code="abc"))

    assert challenges.items[view.challenge_id].attempts == 1


def _use_cases(users=None, challenges=None, gateway=None, events=None):  # noqa: ANN001
    users = users or FakeUsers()
    challenges = challenges or FakeChallenges()
    gateway = gateway or InMemorySecondFactorGateway()
    events = events or InMemoryEventBus()
    return (
        RequestMfaCode(users, challenges, gateway, events),
        VerifyMfaCode(users, challenges, gateway, events),
        users, challenges, events,
    )


def test_agotar_intentos_bloquea_la_operacion():
    request, verify, users, challenges, _ = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))

    for _ in range(MFA_MAX_ATTEMPTS - 1):
        with pytest.raises(UnauthorizedError):
            verify.execute(VerifyMfaCommand(
                user_id=admin.id, purpose=_PURPOSE, code="000000"
            ))
    with pytest.raises(TooManyAttemptsError):
        verify.execute(VerifyMfaCommand(user_id=admin.id, purpose=_PURPOSE, code="000000"))

    assert challenges.items[view.challenge_id].status == "BLOQUEADO"


def test_bloqueado_rechaza_incluso_el_codigo_correcto():
    request, verify, users, challenges, _ = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))
    for _ in range(MFA_MAX_ATTEMPTS):
        with pytest.raises((UnauthorizedError, TooManyAttemptsError)):
            verify.execute(VerifyMfaCommand(
                user_id=admin.id, purpose=_PURPOSE, code="000000"
            ))

    with pytest.raises(TooManyAttemptsError):
        verify.execute(VerifyMfaCommand(
            user_id=admin.id, purpose=_PURPOSE, code=str(view.code)
        ))
    assert challenges.items[view.challenge_id].status == "BLOQUEADO"


def test_codigo_es_de_un_solo_uso():
    request, verify, users, _, _ = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))
    verify.execute(VerifyMfaCommand(user_id=admin.id, purpose=_PURPOSE, code=str(view.code)))

    with pytest.raises(ConflictError):   # ya no hay verificación en curso
        verify.execute(VerifyMfaCommand(
            user_id=admin.id, purpose=_PURPOSE, code=str(view.code)
        ))


def test_sin_desafio_no_hay_nada_que_validar():
    _, verify, users, _, _ = _use_cases()
    admin = _admin(users)
    with pytest.raises(ConflictError):
        verify.execute(VerifyMfaCommand(user_id=admin.id, purpose=_PURPOSE, code="123456"))


def test_cuenta_inexistente_da_404():
    request, verify, _, _, _ = _use_cases()
    with pytest.raises(NotFoundError):
        request.execute(RequestMfaCommand(user_id="0" * 24, purpose=_PURPOSE))
    with pytest.raises(NotFoundError):
        verify.execute(VerifyMfaCommand(user_id="0" * 24, purpose=_PURPOSE, code="123456"))


# ---- Flujo E: el servicio no está disponible ----
def test_sin_servicio_no_se_autoriza_y_el_desafio_queda_bloqueado():
    request, _, users, challenges, events = _use_cases()
    admin = _admin(users)
    view = request.execute(RequestMfaCommand(user_id=admin.id, purpose=_PURPOSE))
    bloqueos = []
    events.subscribe(MfaVerificationLocked, bloqueos.append)

    with pytest.raises(ForbiddenError):
        ResetMfaOnServiceUnavailable(challenges, events).execute(
            ServiceUnavailableCommand(user_id=admin.id, purpose=_PURPOSE)
        )

    assert challenges.items[view.challenge_id].status == "BLOQUEADO"
    assert len(bloqueos) == 1
    # Y no se puede "aprobar por otro camino": no queda nada pendiente.
    assert challenges.get_pending_by_user(admin.id, _PURPOSE) is None


def test_sin_servicio_y_sin_desafio_tambien_se_niega():
    _, _, users, challenges, events = _use_cases()
    admin = _admin(users)
    with pytest.raises(ConflictError):
        ResetMfaOnServiceUnavailable(challenges, events).execute(
            ServiceUnavailableCommand(user_id=admin.id, purpose=_PURPOSE)
        )
