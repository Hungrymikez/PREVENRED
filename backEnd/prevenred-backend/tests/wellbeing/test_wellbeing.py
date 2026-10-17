"""Pruebas de `wellbeing`: anonimato de la encuesta y consentimiento revocable (CU-23/24)."""
from datetime import UTC, datetime

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from prevenred.shared.domain.errors import ConflictError, ValidationError
from prevenred.wellbeing.domain.entities import Consent, SurveyResponse, week_key
from prevenred.wellbeing.infrastructure.mongo_wellbeing_repository import (
    SURVEYS,
    MongoConsentRepository,
    MongoSurveyRepository,
)

USER = str(ObjectId())
MONDAY = datetime(2026, 10, 5, 9, tzinfo=UTC)


def _response(created_at: datetime = MONDAY, **extra) -> SurveyResponse:
    return SurveyResponse(
        answers={"animo": 3, "carga": 4},
        pseudonym="hash-irreversible-abc",
        created_at=created_at,
        **extra,
    )


def _consent(**extra) -> Consent:
    return Consent(
        user_id=USER,
        purpose="ANALITICA_BIENESTAR",
        privacy_notice_version="1.0",
        granted_at=MONDAY,          # fecha fija: comparar con `revoked_at` es determinista
        **extra,
    )


# ----------------------------------------------------------------- dominio
def test_la_encuesta_no_guarda_quien_respondio():  # RN-03
    # El dominio ni siquiera admite el campo: pasarlo es un TypeError.
    with pytest.raises(TypeError):
        _response(respondent_id=USER)
    assert not hasattr(_response(), "respondent_id")


@pytest.mark.parametrize("value", [0, 6, True, "alto"])
def test_escala_fuera_de_1_a_5_se_rechaza(value):
    with pytest.raises(ValidationError):
        SurveyResponse(answers={"animo": value}, pseudonym="hash")


def test_clave_de_semana_iso():
    assert week_key(MONDAY) == "2026-W41"
    assert week_key(datetime(2026, 10, 11, 23, tzinfo=UTC)) == "2026-W41"


def test_solo_un_envio_por_semana():
    response = _response()
    assert response.already_sent_this_week(None) is False
    assert response.already_sent_this_week(datetime(2026, 10, 7, 9, tzinfo=UTC))
    assert response.already_sent_this_week(datetime(2026, 10, 20, 9, tzinfo=UTC)) is False


def test_revocar_dos_veces_no_es_posible():
    consent = _consent()
    consent.revoke(MONDAY)
    assert not consent.active and consent.granted is False
    with pytest.raises(ValidationError):
        consent.revoke(MONDAY)


def test_una_revocacion_anterior_a_la_concesion_se_rechaza():
    with pytest.raises(ValidationError):
        _consent(revoked_at=datetime(2026, 10, 1, tzinfo=UTC))


# ------------------------------------------------------------ repositorio
def test_documento_de_encuesta_solo_tiene_campos_anonimos(db):
    MongoSurveyRepository(db).add(_response())
    doc = db[SURVEYS].find_one({})
    assert "userId" not in doc and "respondentId" not in doc
    assert doc["pseudonym"] == "hash-irreversible-abc" and doc["weekKey"] == "2026-W41"


def test_no_se_pueden_enviar_dos_respuestas_en_la_misma_semana(db):
    repo = MongoSurveyRepository(db)
    repo.add(_response(MONDAY))
    with pytest.raises(DuplicateKeyError):
        repo.add(_response(datetime(2026, 10, 9, 18, tzinfo=UTC)))

    repo.add(_response(datetime(2026, 10, 14, 18, tzinfo=UTC)))  # semana siguiente: sí
    assert repo.count_between(MONDAY, datetime(2026, 10, 31, tzinfo=UTC)) == 2


def test_ultimo_envio_por_pseudonimo(db):
    repo = MongoSurveyRepository(db)
    assert repo.last_response_at("hash-irreversible-abc") is None
    repo.add(_response(MONDAY))
    assert repo.last_response_at("hash-irreversible-abc") == MONDAY


def test_consentimiento_vigente_es_uno_por_finalidad(db):
    repo = MongoConsentRepository(db)
    repo.add(_consent())
    assert repo.find_active(USER, "ANALITICA_BIENESTAR") is not None
    # Un segundo consentimiento VIGENTE de la misma finalidad no se admite.
    with pytest.raises(ConflictError):
        repo.add(_consent())


def test_revocar_libera_el_slot_y_guarda_la_fecha(db):
    revoked_at = datetime(2026, 10, 16, 9, tzinfo=UTC)   # posterior a la concesión
    repo, consent = MongoConsentRepository(db), _consent()
    repo.add(consent)

    consent.revoke(revoked_at)
    repo.update(consent)

    assert repo.find_active(USER, "ANALITICA_BIENESTAR") is None
    history = repo.list_by_user(USER)
    assert history[0].revoked_at == revoked_at and not history[0].granted
    # Tras revocar, se puede volver a aceptar el aviso.
    repo.add(_consent())
    assert repo.find_active(USER, "ANALITICA_BIENESTAR") is not None
