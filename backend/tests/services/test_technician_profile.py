"""El re-registro del técnico pasa por la entidad antes de tocar Mongo."""
import pytest
from bson import ObjectId

from prevenred.services.application.save_technician_profile import (
    SaveTechnicianProfile,
    SaveTechnicianProfileCommand,
)
from prevenred.services.infrastructure.mongo_technician_repository import (
    MongoTechnicianRepository,
)
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.ids import new_id


def test_actualizar_perfil_invalido_no_pisa_lo_guardado(db):
    repo = MongoTechnicianRepository(db)
    use_case = SaveTechnicianProfile(repo)
    user_id = new_id()
    use_case.execute(SaveTechnicianProfileCommand(user_id, ["electricidad"], 4, "hoy"))

    with pytest.raises(ValidationError):
        use_case.execute(SaveTechnicianProfileCommand(user_id, [], 9, "manana"))

    saved = repo.get_by_user_id(user_id)
    assert saved is not None
    assert saved.specialties == ["electricidad"]
    assert saved.experience_years == 4


def test_cambiar_especialidad_de_verificado_vuelve_a_pendiente(db):
    repo = MongoTechnicianRepository(db)
    use_case = SaveTechnicianProfile(repo)
    user_id = new_id()
    created = use_case.execute(SaveTechnicianProfileCommand(user_id, ["obra"], 2, "hoy"))
    db["technicians"].update_one(
        {"_id": ObjectId(created.id)},
        {"$set": {"verificationStatus": "VERIFICADO"}},
    )

    updated = use_case.execute(SaveTechnicianProfileCommand(user_id, ["plomeria"], 2, "hoy"))
    assert updated.verification_status == "PENDIENTE"
