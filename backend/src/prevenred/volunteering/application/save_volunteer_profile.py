"""CU-43 · Guardar perfil de voluntario sin saltarse el dominio."""
from dataclasses import dataclass

from prevenred.volunteering.domain.repositories import VolunteerRepository
from prevenred.volunteering.domain.volunteer import Volunteer


@dataclass(frozen=True)
class SaveVolunteerProfileCommand:
    """Datos que el voluntario envía al crear o actualizar su perfil."""
    user_id: str
    skills: list[str]
    availability: str
    latitude: float
    longitude: float


class SaveVolunteerProfile:
    """Crea el perfil o lo actualiza cargando antes la entidad."""

    def __init__(self, volunteers: VolunteerRepository) -> None:
        self._volunteers = volunteers

    def execute(self, cmd: SaveVolunteerProfileCommand) -> Volunteer:
        """Recupera el perfil, aplica las reglas y solo entonces lo persiste."""
        current = self._volunteers.get_by_user_id(cmd.user_id)
        if current is None:
            created = Volunteer.register(
                user_id=cmd.user_id,
                skills=cmd.skills,
                availability=cmd.availability,
                latitude=cmd.latitude,
                longitude=cmd.longitude,
            )
            self._volunteers.add(created)
            return created
        current.update_profile(
            skills=cmd.skills,
            availability=cmd.availability,
            latitude=cmd.latitude,
            longitude=cmd.longitude,
        )
        self._volunteers.update(current)
        return current
