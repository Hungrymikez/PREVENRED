"""CU-17 · Guardar perfil de técnico sin saltarse el dominio."""
from dataclasses import dataclass

from prevenred.services.domain.repositories import TechnicianRepository
from prevenred.services.domain.technician import Technician


@dataclass(frozen=True)
class SaveTechnicianProfileCommand:
    """Datos que el técnico envía al crear o actualizar su perfil."""
    user_id: str
    specialties: list[str]
    experience_years: int
    availability: str


class SaveTechnicianProfile:
    """Crea el perfil o lo actualiza cargando antes la entidad."""

    def __init__(self, technicians: TechnicianRepository) -> None:
        self._technicians = technicians

    def execute(self, cmd: SaveTechnicianProfileCommand) -> Technician:
        """Recupera el perfil, aplica las reglas y solo entonces lo persiste."""
        current = self._technicians.get_by_user_id(cmd.user_id)
        if current is None:
            created = Technician.register(
                user_id=cmd.user_id,
                specialties=cmd.specialties,
                experience_years=cmd.experience_years,
                availability=cmd.availability,
            )
            self._technicians.add(created)
            return created
        current.update_profile(
            specialties=cmd.specialties,
            experience_years=cmd.experience_years,
            availability=cmd.availability,
        )
        self._technicians.update(current)
        return current
