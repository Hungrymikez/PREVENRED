"""
CU-01 · Registrarse.
Un caso de uso = una clase con un método `execute`. Orquesta: valida, usa el
dominio, guarda, confirma y publica eventos. No contiene reglas de negocio
(esas viven en la entidad User).
"""
from dataclasses import dataclass

from prevenred.identity.application.ports import PasswordHasher
from prevenred.identity.domain.repositories import UserRepository
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email, validate_password_strength
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.domain.errors import ConflictError


@dataclass(frozen=True)
class RegisterUserCommand:
    """Datos de entrada del caso de uso (ya sin detalles de HTTP)."""
    full_name: str
    email: str
    password: str
    #: Uno o varios roles elegidos en el formulario (la persona puede ser Técnico y
    #: Voluntario a la vez). Se guardan todos; el efectivo es el de mayor privilegio.
    roles: tuple[Role, ...]
    neighborhood: str
    privacy_notice_version: str
    accepted_terms: bool


class RegisterUser:
    """Caso de uso CU-01: crea una cuenta de Ciudadano o de Técnico/Voluntario."""
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        events: EventBus,
    ) -> None:
        self._users, self._hasher, self._events = users, hasher, events

    def execute(self, cmd: RegisterUserCommand) -> User:
        """Crea la cuenta.

        Valida los datos, verifica que el correo no exista, guarda el usuario y publica sus eventos.
        """
        email = Email(cmd.email)                    # paso 4: valida formato
        validate_password_strength(cmd.password)

        # E1: el medio de contacto ya está registrado.
        if self._users.get_by_email(email) is not None:
            raise ConflictError("Ese correo ya está registrado. Puedes recuperar tu acceso.")

        user = User.register(                       # pasos 5-6: reglas en el dominio
            full_name=cmd.full_name,
            email=email,
            password_hash=self._hasher.hash(cmd.password),
            roles=cmd.roles,
            neighborhood=cmd.neighborhood,
            privacy_notice_version=cmd.privacy_notice_version,
            accepted_terms=cmd.accepted_terms,
        )
        # En MongoDB escribir UN documento es atómico: no hace falta transacción.
        self._users.add(user)
        for event in user.pull_events():            # solo después de guardar
            self._events.publish(event)
        return user
