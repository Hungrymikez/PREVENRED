"""Pruebas de INFRAESTRUCTURA de CU-03 y CU-08 contra Mongo (mongomock)."""
from datetime import timedelta

import pytest
from bson import ObjectId

from prevenred.identity.application.security import hash_one_time_code
from prevenred.identity.domain.mfa import CODE_TTL, MfaChallenge
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email, OneTimeCode, SecondFactorMethod
from prevenred.identity.infrastructure.indexes import ensure_indexes
from prevenred.identity.infrastructure.mongo_mfa_challenge_repository import (
    COLLECTION as MFA_CHALLENGES,
)
from prevenred.identity.infrastructure.mongo_mfa_challenge_repository import (
    MongoMfaChallengeRepository,
)
from prevenred.identity.infrastructure.mongo_role_audit import MongoRoleAssignmentAudit
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.identity.infrastructure.second_factor_gateway import (
    InMemorySecondFactorGateway,
)
from prevenred.shared.domain.errors import ConflictError, UnauthorizedError
from prevenred.shared.domain.events import utcnow

_SECRET = "enc:v1:secreto"
_CODE = "482913"


def _admin(email="admin@prevenred.gov.co") -> User:
    """Cuenta administrativa existente (la crea un Administrador, CU-08)."""
    return User.open_administratively(
        full_name="Ana Admin", email=Email(email), password_hash="h",
        roles=(Role.ADMINISTRADOR,), neighborhood="Centro", privacy_notice_version="v1",
        created_by="a" * 24,
    )


def _challenge(user: User, *, purpose="cambio_de_modo", code=_CODE) -> MfaChallenge:
    return MfaChallenge.open(
        user_id=user.id, role=Role.ADMINISTRADOR, purpose=purpose,
        method=SecondFactorMethod("totp"),
        code_hash=hash_one_time_code(code), secret_enc=_SECRET,
    )


# ---- CU-08: cuentas administrativas ----
def test_guarda_una_cuenta_administrativa(db):
    repo = MongoUserRepository(db)
    admin = _admin()
    repo.add(admin)

    stored = repo.get_by_id(admin.id)
    assert stored.role is Role.ADMINISTRADOR
    assert db["users"].find_one({"email": admin.email.value})["roles"] == ["ADMINISTRADOR"]


def test_cuenta_el_administrador_activo_para_el_ultimo_admin(db):  # E1
    repo = MongoUserRepository(db)
    repo.add(_admin("uno@prevenred.gov.co"))
    first = repo.get_by_email(Email("uno@prevenred.gov.co"))
    assert repo.count_active_with_role(Role.ADMINISTRADOR.value) == 1
    assert repo.would_leave_platform_without_admins(first.id)

    repo.add(_admin("dos@prevenred.gov.co"))
    assert repo.count_active_with_role(Role.ADMINISTRADOR.value) == 2
    assert not repo.would_leave_platform_without_admins(first.id)


def test_una_cuenta_suspendida_no_cuenta(db):
    repo = MongoUserRepository(db)
    admin = _admin()
    repo.add(admin)
    admin.suspend()
    repo.update(admin)
    assert repo.count_active_with_role(Role.ADMINISTRADOR.value) == 0


def test_indice_unico_de_correo_sigue_protegiendo(db):
    repo = MongoUserRepository(db)
    repo.add(_admin())
    with pytest.raises(ConflictError):
        repo.add(_admin())


# ---- CU-03: desafíos del segundo factor ----
def test_guarda_y_lee_el_desafio(db):
    users, challenges = MongoUserRepository(db), MongoMfaChallengeRepository(db)
    admin = _admin()
    users.add(admin)
    challenge = _challenge(admin)
    challenges.add(challenge)

    stored = challenges.get_pending_by_user(admin.id, "cambio_de_modo")
    assert stored is not None and stored.id == challenge.id
    assert stored.status == "PENDIENTE" and stored.attempts == 0
    assert stored.method.value == "TOTP"
    # El código queda como HASH en la base, nunca en claro.
    doc = db[MFA_CHALLENGES].find_one({"_id": ObjectId(challenge.id)})
    assert doc["codeHash"] == hash_one_time_code(_CODE)
    assert _CODE not in str(doc)


def test_no_devuelve_desafios_de_otra_operacion(db):
    users, challenges = MongoUserRepository(db), MongoMfaChallengeRepository(db)
    admin = _admin()
    users.add(admin)
    challenges.add(_challenge(admin, purpose="cambio_de_modo"))
    assert challenges.get_pending_by_user(admin.id, "otra_operacion") is None


def test_guarda_el_avance_del_desafio(db):
    users, challenges = MongoUserRepository(db), MongoMfaChallengeRepository(db)
    admin = _admin()
    users.add(admin)
    challenges.add(_challenge(admin))

    stored = challenges.get_pending_by_user(admin.id, "cambio_de_modo")
    with pytest.raises(UnauthorizedError):        # código incorrecto (E1)
        stored.verify(None, code_matches=False)
    challenges.update(stored)

    after = challenges.get_by_id(stored.id)
    assert after.attempts == 1 and after.status == "PENDIENTE"


def test_verificacion_satisfecha_se_encuentra_por_fecha(db):
    users, challenges = MongoUserRepository(db), MongoMfaChallengeRepository(db)
    admin = _admin()
    users.add(admin)
    challenge = _challenge(admin, purpose="admin_users")
    challenges.add(challenge)
    challenge.verify(_CODE, code_matches=True)
    challenges.update(challenge)

    assert challenges.get_pending_by_user(admin.id, "admin_users") is None
    found = challenges.get_latest_verified(
        admin.id, "admin_users", since=utcnow() - timedelta(minutes=10)
    )
    assert found is not None and found.is_satisfied
    # Fuera de la ventana ya no autoriza nada (CU-08 exige verificación reciente).
    assert challenges.get_latest_verified(
        admin.id, "admin_users", since=utcnow() + timedelta(minutes=1)
    ) is None


def test_expira_los_desafios_vencidos(db):
    users, challenges = MongoUserRepository(db), MongoMfaChallengeRepository(db)
    admin = _admin()
    users.add(admin)
    challenge = _challenge(admin)
    challenges.add(challenge)
    # Se vence el documento directamente (como si hubiera pasado el tiempo): la
    # entidad es inmutable por dentro, pero el adaptador debe cerrarlo igual.
    past = utcnow() - timedelta(seconds=1)
    db[MFA_CHALLENGES].update_one({"_id": ObjectId(challenge.id)}, {"$set": {"expiresAt": past}})

    challenges.expire_stale(admin.id)

    assert challenges.get_pending_by_user(admin.id, "cambio_de_modo") is None
    # El TTL de `expiresAt` borra o el adaptador cierra: en ningún caso sigue pendiente.
    doc = db[MFA_CHALLENGES].find_one({})
    assert doc is None or doc["status"] == "EXPIRADO"


def test_encuentra_el_bloqueo_reciente(db):  # E2
    users, challenges = MongoUserRepository(db), MongoMfaChallengeRepository(db)
    admin = _admin()
    users.add(admin)
    challenge = _challenge(admin)
    challenges.add(challenge)
    challenge.status = "BLOQUEADO"
    challenges.update(challenge)

    assert challenges.get_blocked_by_user(
        admin.id, "cambio_de_modo", since=utcnow() - CODE_TTL
    ) is not None



# ---- CU-05: auditoría de CU-08 ----
def test_auditoria_guarda_el_cambio_sin_datos_personales(db):  # E3 / RN-05
    audit = MongoRoleAssignmentAudit(db)
    audit.record(
        actor_id="a" * 24, action="USER_ROLE_CHANGED", target_id="b" * 24,
        details={"previousRole": "TECNICO", "newRole": "INSPECTOR"},
    )
    doc = db["audit_logs"].find_one({})
    assert doc["action"] == "USER_ROLE_CHANGED"
    assert doc["resource"] == "users" and doc["result"] == "SUCCESS"
    assert doc["details"] == {"previousRole": "TECNICO", "newRole": "INSPECTOR"}
    assert "email" not in doc["details"] and "name" not in doc["details"]


# ---- Índices ----
def test_indices_de_mfa_y_auditoria(db):
    ensure_indexes(db)      # idempotente: se puede repetir sin error
    challenge_indexes = {i["name"] for i in db[MFA_CHALLENGES].list_indexes()}
    assert "ix_mfa_challenges_user_purpose_status" in challenge_indexes
    assert "ttl_mfa_challenges_expires" in challenge_indexes
    audit_indexes = {i["name"] for i in db["audit_logs"].list_indexes()}
    assert "ix_audit_actor_created" in audit_indexes
    assert "ix_audit_resource" in audit_indexes
    user_indexes = {i["name"] for i in db["users"].list_indexes()}
    assert "ix_users_role_status" in user_indexes
    # El barrio es campo raíz: el índice apunta a `neighborhood`, no a `location`.
    assert "ix_users_neighborhood" in user_indexes
    by_name = {i["name"]: i for i in db["users"].list_indexes()}
    assert list(by_name["ix_users_neighborhood"]["key"]) == ["neighborhood"]


# ---- Puerto técnico del segundo factor ----
def test_gateway_emite_un_codigo_que_valida_una_sola_vez():
    gateway = InMemorySecondFactorGateway()
    code, secret = gateway.issue_code(secret_enc="", code_hash=hash_one_time_code)
    assert secret.startswith("enc:v1:")                 # nunca en claro
    digest = hash_one_time_code(code.value)
    assert gateway.matches(code=code, code_hash=digest)
    assert not gateway.matches(code=code, code_hash=digest)   # uso único


def test_gateway_rechaza_un_codigo_ajeno():
    gateway = InMemorySecondFactorGateway()
    code, _ = gateway.issue_code(secret_enc=_SECRET, code_hash=hash_one_time_code)
    other = OneTimeCode("000000" if code.value != "000000" else "111111")
    assert not gateway.matches(code=other, code_hash=hash_one_time_code(code.value))

