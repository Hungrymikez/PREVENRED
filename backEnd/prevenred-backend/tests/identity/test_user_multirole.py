"""
Pruebas del MULTIROL (RF-03): una cuenta guarda TODOS sus roles y no los pierde al
actualizarse.

Antes, `rehydrate` se quedaba con `roles[0]` y `update` escribía `[role.value]`: un
Técnico y Voluntario a la vez quedaba guardado solo como Técnico en la primera
actualización. Aquí se prueba explícitamente que no vuelva a pasar.
"""
import pytest

from prevenred.identity.domain.role import (
    PRIVILEGE_ORDER,
    Role,
    highest_privilege_role,
    normalize_roles,
)
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository


def _user(*roles: Role, email="multi@mail.com") -> User:
    return User.register(
        full_name="Marta Multirrol", email=Email(email), password_hash="h", roles=roles,
        neighborhood="Cuba", privacy_notice_version="v1", accepted_terms=True,
    )


def _stored_roles(db, email="multi@mail.com") -> list[str]:
    return db["users"].find_one({"email": email})["roles"]


# ---- El rol efectivo (el de mayor privilegio) ----
def test_registrar_con_tecnico_y_voluntario_guarda_los_dos(db):
    repo = MongoUserRepository(db)
    user = _user(Role.TECNICO, Role.VOLUNTARIO)
    repo.add(user)

    assert _stored_roles(db) == ["TECNICO", "VOLUNTARIO"]
    loaded = repo.get_by_id(user.id)
    assert set(loaded.roles) == {Role.TECNICO, Role.VOLUNTARIO}
    assert loaded.role is Role.TECNICO          # el efectivo, sin tocar el código viejo


def test_ciudadano_y_tecnico_sobreviven_a_una_actualizacion(db):
    """La prueba pedida: guardar [CIUDADANO, TECNICO], actualizar y siguen los dos."""
    repo = MongoUserRepository(db)
    user = _user(Role.CIUDADANO, Role.TECNICO)
    repo.add(user)
    assert _stored_roles(db) == ["TECNICO", "CIUDADANO"]

    # Se lee de la base (como en un caso de uso real), se cambia otra cosa y se guarda.
    loaded = repo.get_by_id(user.id)
    assert set(loaded.roles) == {Role.CIUDADANO, Role.TECNICO}
    loaded.change_name("Marta Multirrol Actualizada")
    loaded.register_device_token("token-celular")
    repo.update(loaded)

    assert _stored_roles(db) == ["TECNICO", "CIUDADANO"]
    after = repo.get_by_id(user.id)
    assert set(after.roles) == {Role.CIUDADANO, Role.TECNICO}
    assert after.full_name == "Marta Multirrol Actualizada"


def test_la_base_ordena_los_roles_de_mayor_a_menor_privilegio(db):
    """Así `roles[0]` es siempre el rol efectivo, también en una consulta a mano."""
    MongoUserRepository(db).add(_user(Role.CIUDADANO, Role.VOLUNTARIO, Role.TECNICO))
    assert _stored_roles(db) == ["TECNICO", "VOLUNTARIO", "CIUDADANO"]


def test_el_rol_efectivo_sigue_el_orden_de_privilegio():
    assert PRIVILEGE_ORDER == (
        Role.CIUDADANO, Role.VOLUNTARIO, Role.TECNICO,
        Role.PROFESIONAL_SALUD, Role.INSPECTOR, Role.ADMINISTRADOR,
    )
    assert highest_privilege_role([Role.CIUDADANO, Role.INSPECTOR]) is Role.INSPECTOR
    assert highest_privilege_role([Role.TECNICO, Role.ADMINISTRADOR]) is Role.ADMINISTRADOR


def test_los_roles_repetidos_se_guardan_una_sola_vez(db):
    MongoUserRepository(db).add(_user(Role.TECNICO, Role.TECNICO))
    assert _stored_roles(db) == ["TECNICO"]


# ---- Reglas de negocio sobre el conjunto de roles ----
def test_una_cuenta_de_administrador_mas_ciudadano_exige_mfa():
    """El rol efectivo manda: si es Administrador, RN-07 exige el segundo factor."""
    user = User.open_administratively(
        full_name="Ana Admin", email=Email("ana@prevenred.gov.co"), password_hash="h",
        roles=(Role.CIUDADANO, Role.ADMINISTRADOR), neighborhood="Centro",
        privacy_notice_version="v1", created_by="a" * 24,
    )
    assert user.role is Role.ADMINISTRADOR
    assert user.requires_mfa() and user.role.is_administrative


def test_el_evento_de_registro_lleva_el_rol_efectivo():
    user = _user(Role.VOLUNTARIO, Role.TECNICO)
    assert user.pull_events()[0].role == "TECNICO"


def test_has_any_role_para_autorizar():
    user = _user(Role.TECNICO, Role.VOLUNTARIO)
    assert user.has_any_role(Role.VOLUNTARIO, Role.INSPECTOR)
    assert not user.has_any_role(Role.ADMINISTRADOR)


def test_no_se_puede_quitar_el_ultimo_rol():
    user = _user(Role.TECNICO)
    user.grant_role(Role.VOLUNTARIO)
    user.revoke_role(Role.TECNICO)
    assert user.roles == (Role.VOLUNTARIO,)


def test_normalize_roles_no_acepta_texto():
    with pytest.raises(TypeError):
        normalize_roles(["TECNICO"])
