"""CU-03: el administrador solo entra sin MFA si el entorno lo permite."""
import pytest

from prevenred.auth.application.login_user import LoginCommand, LoginUser
from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.shared.domain.errors import ForbiddenError
from prevenred.shared.domain.events import utcnow


class _Users:
    def __init__(self, user: User) -> None:
        self.user = user

    def get_by_email(self, email: Email) -> User | None:
        return self.user if self.user.email == email else None

    def update(self, user: User) -> None:
        self.user = user


class _Hasher:
    def verify(self, plain: str, hashed: str) -> bool:
        return plain == "clave-segura-1"


class _Tokens:
    def issue(self, user_id: str, role: Role) -> str:
        return f"token-{role.value}"


def _admin() -> User:
    return User(
        full_name="Ana Admin",
        email=Email("admin@mail.com"),
        password_hash="hash",
        role=Role.ADMINISTRADOR,
        neighborhood="Centro",
        privacy_notice_version="v1",
        terms_accepted_at=utcnow(),
    )


def test_administrador_sin_bypass_no_recibe_token():
    use_case = LoginUser(_Users(_admin()), _Hasher(), _Tokens(), mfa_required=True)
    with pytest.raises(ForbiddenError):
        use_case.execute(LoginCommand(email="admin@mail.com", password="clave-segura-1"))


def test_administrador_en_desarrollo_recibe_token():
    use_case = LoginUser(_Users(_admin()), _Hasher(), _Tokens(), mfa_required=False)
    result = use_case.execute(LoginCommand(email="admin@mail.com", password="clave-segura-1"))
    assert result.access_token == "token-administrador"
    assert result.role is Role.ADMINISTRADOR
