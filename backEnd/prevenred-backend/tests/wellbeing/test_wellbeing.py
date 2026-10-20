"""Pruebas de `wellbeing`: anonimato de la encuesta y consentimiento revocable (CU-23/24)."""
from datetime import UTC, datetime
from pathlib import Path

import pytest
from bson import ObjectId

from prevenred.shared.domain.errors import ConflictError, ValidationError
from prevenred.wellbeing.domain.entities import Consent, SurveyResponse, week_key
from prevenred.wellbeing.infrastructure.mongo_wellbeing_repository import (
    CONSENTS,
    SURVEYS,
    MongoConsentRepository,
    MongoSurveyRepository,
)

USER = str(ObjectId())
MONDAY = datetime(2026, 10, 5, 9, tzinfo=UTC)
PURPOSE = "ANALITICA_BIENESTAR"

#: Nada de esto puede aparecer en un documento de encuesta (RN-03, O-07).
IDENTITY_FIELDS = ("userId", "respondentId", "pseudonym", "respondent_id", "user_id")


def _response(created_at: datetime = MONDAY, **extra) -> SurveyResponse:
    return SurveyResponse(
        answers={"animo": 3, "carga": 4},
        created_at=created_at,
        **extra,
    )


def _consent(**extra) -> Consent:
    return Consent(
        user_id=USER,
        purpose=PURPOSE,
        privacy_notice_version="1.0",
        granted_at=MONDAY,          # fecha fija: comparar con `revoked_at` es determinista
        **extra,
    )


# ----------------------------------------------------------------- dominio
def test_la_encuesta_no_guarda_quien_respondio():  # RN-03
    # El dominio ni siquiera admite esos campos: pasarlos es un TypeError.
    for field in IDENTITY_FIELDS:
        with pytest.raises(TypeError):
            _response(**{field: USER})
    response = _response()
    for field in IDENTITY_FIELDS:
        assert not hasattr(response, field)


@pytest.mark.parametrize("value", [0, 6, True, "alto"])
def test_escala_fuera_de_1_a_5_se_rechaza(value):
    with pytest.raises(ValidationError):
        SurveyResponse(answers={"animo": value})


def test_clave_de_semana_iso():
    assert week_key(MONDAY) == "2026-W41"
    assert week_key(datetime(2026, 10, 11, 23, tzinfo=UTC)) == "2026-W41"


def test_solo_un_envio_por_semana():
    response = _response()
    assert response.was_sent_in(None) is False
    assert response.was_sent_in("2026-W41")
    assert response.was_sent_in("2026-W40") is False
    assert response.was_sent_in("2026-W42") is False


def test_el_consentimiento_solo_guarda_la_semana_del_envio():  # O-08
    consent = _consent()
    assert consent.last_survey_week_key is None
    consent.record_survey_sent(datetime(2026, 10, 7, 23, 45, tzinfo=UTC))
    assert consent.last_survey_week_key == "2026-W41"   # ni hora, ni minuto: sólo la semana


@pytest.mark.parametrize("value", ["2026-10-05", "W41", "2026-W4", ""])
def test_la_semana_del_consentimiento_se_valida(value):
    with pytest.raises(ValidationError):
        _consent(last_survey_week_key=value)


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
def test_documento_de_encuesta_no_tiene_ningun_dato_de_la_persona(db):  # RN-03
    MongoSurveyRepository(db).add(_response(zone="Centro"))
    doc = db[SURVEYS].find_one({})
    for field in IDENTITY_FIELDS:
        assert field not in doc
    # Tampoco guarda la semana: eso vive en `wellbeing_consents`.
    assert "weekKey" not in doc
    assert set(doc) == {"_id", "answers", "zone", "triggerEventId", "createdAt"}


def test_el_limite_semanal_vive_en_el_consentimiento(db):  # O-08
    consents = MongoConsentRepository(db)
    consents.add(_consent())

    # Antes de responder: no hay semana registrada.
    assert consents.find_active(USER, PURPOSE).last_survey_week_key is None

    consents.record_survey_sent(USER, PURPOSE, "2026-W41")
    assert consents.find_active(USER, PURPOSE).last_survey_week_key == "2026-W41"
    # Lo guardado es la semana en texto, no una fecha: no hay hora del envío.
    doc = db[CONSENTS].find_one({"userId": ObjectId(USER)})
    assert doc["lastSurveyWeekKey"] == "2026-W41"
    assert not isinstance(doc["lastSurveyWeekKey"], datetime)

    # Repetir la misma semana no cambia nada, y una semana anterior no retrocede.
    consents.record_survey_sent(USER, PURPOSE, "2026-W41")
    consents.record_survey_sent(USER, PURPOSE, "2026-W40")
    assert consents.find_active(USER, PURPOSE).last_survey_week_key == "2026-W41"

    # La semana siguiente sí avanza.
    consents.record_survey_sent(USER, PURPOSE, "2026-W42")
    assert consents.find_active(USER, PURPOSE).last_survey_week_key == "2026-W42"


def test_la_regla_semanal_se_consulta_con_una_sola_semana(db):
    # El servicio comprueba con la semana del consentimiento, sin tocar la encuesta.
    consents, surveys = MongoConsentRepository(db), MongoSurveyRepository(db)
    consents.add(_consent())
    consents.record_survey_sent(USER, PURPOSE, "2026-W41")

    last_week = consents.find_active(USER, PURPOSE).last_survey_week_key
    assert _response(MONDAY).was_sent_in(last_week) is True
    assert _response(datetime(2026, 10, 14, 18, tzinfo=UTC)).was_sent_in(last_week) is False

    # Y la encuesta no permite preguntar nada sobre la persona.
    assert not hasattr(surveys, "last_response_at")


def test_se_pueden_enviar_varias_respuestas_anonimas(db):
    # Ya no hay índice único por pseudónimo: dos documentos anónimos conviven
    # aunque sean de la misma zona y semana; el límite lo pone el consentimiento.
    repo = MongoSurveyRepository(db)
    repo.add(_response(MONDAY, zone="Centro"))
    repo.add(_response(MONDAY, zone="Centro"))
    assert repo.count_between(MONDAY, datetime(2026, 10, 31, tzinfo=UTC)) == 2


def test_indices_de_bienestar_no_indexan_a_la_persona_en_la_encuesta(db):
    # `index_information()` se indexa por NOMBRE del índice.
    survey_names = set(db[SURVEYS].index_information())
    assert "uq_surveys_pseudonym_week" not in survey_names
    assert survey_names == {"_id_", "ix_surveys_zone_created", "ix_surveys_created"}
    for info in db[SURVEYS].index_information().values():
        assert all(field not in IDENTITY_FIELDS for field, _ in info["key"])

    consent_names = set(db[CONSENTS].index_information())
    assert "ix_consent_user_survey_week" in consent_names


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


# ------------------------------------------------------- regresión en el código
def test_el_codigo_de_bienestar_no_vuelve_a_usar_un_pseudonimo():
    # Si alguien reintroduce el hash "seudónimo" (campo, parámetro o índice), este
    # test avisa: la encuesta no debe tener NINGÚN punto de unión con una persona
    # (RN-03). Sólo mira el código; los README hablan de él para prohibirlo.
    raiz = Path(__file__).resolve().parents[2]
    for archivo in (raiz / "src" / "prevenred" / "wellbeing").rglob("*.py"):
        codigo = archivo.read_text(encoding="utf-8").lower()
        assert "pseudonym" not in codigo, f"{archivo.name} vuelve a usar pseudonym"
