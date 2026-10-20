"""El re-registro del voluntario pasa por la entidad antes de tocar Mongo."""
import pytest

from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.ids import new_id
from prevenred.volunteering.application.save_volunteer_profile import (
    SaveVolunteerProfile,
    SaveVolunteerProfileCommand,
)
from prevenred.volunteering.infrastructure.mongo_volunteer_repository import (
    MongoVolunteerRepository,
)


def test_actualizar_perfil_invalido_no_pisa_lo_guardado(db):
    repo = MongoVolunteerRepository(db)
    use_case = SaveVolunteerProfile(repo)
    user_id = new_id()
    use_case.execute(SaveVolunteerProfileCommand(
        user_id, ["primeros auxilios"], "hoy", 4.81, -75.69,
    ))

    with pytest.raises(ValidationError):
        use_case.execute(SaveVolunteerProfileCommand(user_id, [], "manana", 4.81, -75.69))

    saved = repo.get_by_user_id(user_id)
    assert saved is not None
    assert saved.skills == ["primeros auxilios"]
    assert saved.availability == "hoy"
