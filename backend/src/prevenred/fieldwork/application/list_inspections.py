"""CU-35 · Consultar censos e inspecciones de inmuebles."""

from prevenred.auth.application.ports import TokenPayload
from prevenred.shared.domain.errors import ForbiddenError

from ..domain.inspection import PropertyInspection
from ..domain.repositories import FieldworkRepository


class ListInspections:
    """El inspector ve sus propias inspecciones; el administrador ve todas (las más recientes)."""

    def __init__(self, repository: FieldworkRepository) -> None:
        self._repository = repository

    def execute(self, requester: TokenPayload, limit: int = 100) -> list[PropertyInspection]:
        role = requester.role.value
        if role == "administrador":
            return self._repository.list_recent(limit)
        if role == "inspector":
            return self._repository.list_by_inspector(requester.user_id)[:limit]
        raise ForbiddenError("Solo evaluadores de campo o administradores pueden ver los censos.")
