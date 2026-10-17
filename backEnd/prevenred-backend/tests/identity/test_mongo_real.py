"""Misma garantía de correo único, pero contra MongoDB real (se omite si no hay MONGO_TEST_URI)."""
import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.indexes import ensure_indexes
from prevenred.identity.infrastructure.mongo_user_repository import MongoUserRepository
from prevenred.shared.domain.errors import ConflictError


def test_correo_unico_en_mongo_real(real_db):
    ensure_indexes(real_db)
    repo = MongoUserRepository(real_db)

    def new():
        return User.register(
            full_name="Luis Mora", email=Email("luis@mail.com"), password_hash="h",
            roles=(Role.CIUDADANO,), neighborhood="Cuba", privacy_notice_version="v1",
            accepted_terms=True,
        )

    repo.add(new())
    with pytest.raises(ConflictError):
        repo.add(new())
    assert repo.get_by_email(Email("luis@mail.com")).locked_until is None
