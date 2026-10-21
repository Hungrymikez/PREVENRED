"""Consulta el modo operacional vigente (RF-02)."""

from ..domain.mode import OperationalMode
from ..domain.repositories import OperationalModeRepository


class GetCurrentOperationalMode:
    """Caso de uso: obtener el estado operacional global actual."""

    def __init__(self, repository: OperationalModeRepository) -> None:
        self._repository = repository

    def execute(self) -> OperationalMode:
        return self._repository.get_current_mode()
