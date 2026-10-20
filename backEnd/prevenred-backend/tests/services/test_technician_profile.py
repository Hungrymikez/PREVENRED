"""Pruebas de `services`: verificación del técnico y búsqueda por especialidad (CU-17/18/19)."""
from datetime import UTC, datetime

import pytest
from bson import ObjectId

from prevenred.services.domain.entities import TechnicianProfile
from prevenred.services.infrastructure.mongo_technician_repository import (
    MongoTechnicianRepository,
)
from prevenred.shared.domain.errors import ConflictError, ValidationError

ADMIN = str(ObjectId())


def _profile(user_id: str | None = None, **extra) -> TechnicianProfile:
    return TechnicianProfile(
        user_id=user_id or str(ObjectId()),
        specialties=extra.pop("specialties", ("PLOMERIA",)),
        experience_years=extra.pop("experience_years", 5),
        **extra,
    )


# ----------------------------------------------------------------- dominio
def test_un_tecnico_nace_pendiente_de_verificacion():
    profile = _profile()
    assert profile.verification_status == "PENDIENTE" and not profile.verified


def test_sin_documentos_no_se_puede_verificar():  # CU-18
    with pytest.raises(ValidationError):
        _profile().verify(ADMIN)


def test_subir_documentos_nuevos_reinicia_la_verificacion():  # CU-17
    profile = _profile(documents=("doc-1",))
    profile.verify(ADMIN)
    assert profile.verified

    profile.attach_documents(("doc-2",))
    assert profile.verification_status == "PENDIENTE"
    assert profile.verified_by is None and profile.verified_at is None
    # Los documentos previos no se pierden y no se duplican.
    assert profile.documents == ("doc-1", "doc-2")


def test_adjuntar_documentos_vacios_es_un_error():
    with pytest.raises(ValidationError):
        _profile().attach_documents(())


def test_rechazo_guarda_el_motivo():  # CU-18
    profile = _profile(documents=("doc-1",))
    profile.reject(ADMIN, "La cédula no es legible", at=datetime(2026, 10, 1, tzinfo=UTC))
    assert profile.verification_status == "RECHAZADO"
    assert profile.rejection_reason == "La cédula no es legible"
    assert profile.rejection_reason and not profile.verified


@pytest.mark.parametrize("rating", [-0.1, 5.1])
def test_calificacion_fuera_de_rango_no_se_acepta(rating):
    with pytest.raises(ValidationError):
        _profile(rating=rating)


def test_especialidades_no_se_repiten():
    with pytest.raises(ValidationError):
        _profile(specialties=("PLOMERIA", "PLOMERIA"))


# ------------------------------------------------------------ repositorio
def test_un_usuario_solo_tiene_un_perfil(db):
    repo, user_id = MongoTechnicianRepository(db), str(ObjectId())
    repo.add(_profile(user_id))
    with pytest.raises(ConflictError):
        repo.add(_profile(user_id))


def test_verificacion_se_persiste_y_aparece_en_la_cola(db):
    repo, profile = MongoTechnicianRepository(db), _profile(documents=("doc-1",))
    repo.add(profile)
    assert [p.id for p in repo.list_verification_queue()] == [profile.id]

    profile.verify(ADMIN)
    repo.update(profile)

    loaded = repo.get_by_user_id(profile.user_id)
    assert loaded.verified and loaded.verified_by == ADMIN
    assert repo.list_verification_queue() == []


def test_busqueda_solo_muestra_perfiles_verificados(db):
    repo = MongoTechnicianRepository(db)
    verified = _profile(specialties=("ELECTRICIDAD",), documents=("doc-1",))
    verified.verify(ADMIN)
    repo.add(verified)
    repo.add(_profile(specialties=("ELECTRICIDAD",), documents=("doc-1",)))

    found = repo.search(specialty="ELECTRICIDAD")
    assert [p.id for p in found] == [verified.id]


def test_busqueda_por_especialidad_ignora_otras(db):
    repo = MongoTechnicianRepository(db)
    profile = _profile(specialties=("CARPINTERIA",), documents=("doc-1",))
    profile.verify(ADMIN)
    repo.add(profile)

    assert repo.search(specialty="PLOMERIA") == []
