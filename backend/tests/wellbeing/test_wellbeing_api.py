"""Caja blanca de Mente Resiliente: router + repositorio Motor + reglas de triage y k-anonimato."""

import pytest

from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId
from prevenred.wellbeing.domain.consent import WellbeingConsent
from prevenred.wellbeing.domain.survey import WellbeingSurvey

BASE = "/api/v1/wellbeing"


def _survey(api, neighborhood="Cuba", mood=3, text=""):
    return api.post(
        f"{BASE}/surveys", json={"neighborhood": neighborhood, "mood_score": mood, "text": text}
    )


# ---------- Guard clause de consentimiento (RF-14 / RN-05) ----------


def test_encuesta_sin_consentimiento_responde_403(api, act_as, make_user):
    act_as(make_user())
    r = _survey(api)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_consentimiento_revocado_bloquea_la_encuesta(api, act_as, make_user, motor_db):
    user = act_as(make_user())
    assert api.post(f"{BASE}/consent", json={}).status_code == 200
    motor_db["wellbeing_consents"]._col.update_one(
        {"user_id": user.id}, {"$set": {"is_revoked": True}}
    )
    assert _survey(api).status_code == 403


def test_renovar_consentimiento_actualiza_el_mismo_documento(api, act_as, make_user, motor_db):
    """Regresión: antes se reemplazaba el documento con otro _id y MongoDB fallaba (500)."""
    user = act_as(make_user())
    first = api.post(f"{BASE}/consent", json={})
    second = api.post(f"{BASE}/consent", json={"terms_version": "v2.0"})

    assert first.status_code == second.status_code == 200
    assert second.json()["user_id"] == user.id
    assert second.json()["terms_version"] == "v2.0"
    docs = list(motor_db["wellbeing_consents"]._col.find({"user_id": user.id}))
    assert len(docs) == 1
    assert docs[0]["terms_version"] == "v2.0"


# ---------- Triage de crisis (RF-18) ----------


@pytest.mark.parametrize(
    "text",
    [
        "Ya no quiero vivir después de la inundación",
        "pensé en el SUICIDIO anoche",
        "tengo ganas de cortarme",
        "siento desesperación total, no tengo salida",
        "No puedo mas con esto",
    ],
)
def test_texto_con_senales_de_crisis_activa_canalizacion(api, act_as, make_user, text):
    act_as(make_user())
    api.post(f"{BASE}/consent", json={})
    r = _survey(api, mood=1, text=text)
    assert r.status_code == 201
    body = r.json()
    assert body["crisis_detected"] is True
    assert "106" in body["crisis_support_message"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Hoy estoy tranquilo con mi familia",
        "suicidas",  # casi-coincidencia: el patrón exige el prefijo 'suicidi'
        "no puedo moverme",  # casi-coincidencia de 'no puedo más'
    ],
)
def test_texto_sin_crisis_no_emite_mensaje(api, act_as, make_user, text):
    act_as(make_user())
    api.post(f"{BASE}/consent", json={})
    body = _survey(api, text=text).json()
    assert body["crisis_detected"] is False
    assert body["crisis_support_message"] is None


def test_detectores_con_texto_vacio_cortocircuitan():
    assert WellbeingSurvey._detect_crisis("") is False
    assert WellbeingSurvey._sanitize_pii("") == ""


def test_pii_se_enmascara_antes_de_persistir(api, act_as, make_user, motor_db):
    act_as(make_user())
    api.post(f"{BASE}/consent", json={})
    _survey(api, text="escribe a ana@mail.com o al 3101234567, cédula 1088123456")
    stored = motor_db["wellbeing_surveys"]._col.find_one()
    assert stored["sanitized_text"] == (
        "escribe a [CORREO_PROTEGIDO] o al [TEL_PROTEGIDO], cédula [ID_PROTEGIDO]"
    )


# ---------- Boundary testing de la escala de ánimo y el barrio ----------


@pytest.mark.parametrize(("mood", "status"), [(0, 422), (1, 201), (5, 201), (6, 422)])
def test_limites_de_escala_de_animo_en_api(api, act_as, make_user, mood, status):
    act_as(make_user())
    api.post(f"{BASE}/consent", json={})
    assert _survey(api, mood=mood).status_code == status


@pytest.mark.parametrize("mood", [0, 6])
def test_limites_de_escala_de_animo_en_dominio(mood):
    with pytest.raises(DomainValidationError):
        WellbeingSurvey.create(user_id=EntityId.generate(), neighborhood="Cuba", mood_score=mood)


@pytest.mark.parametrize("neighborhood", ["", " ", "A "])
def test_barrio_demasiado_corto_en_dominio(neighborhood):
    with pytest.raises(DomainValidationError):
        WellbeingSurvey.create(user_id=EntityId.generate(), neighborhood=neighborhood, mood_score=3)


def test_consentimiento_sin_version_es_invalido():
    with pytest.raises(DomainValidationError):
        WellbeingConsent.create(user_id=EntityId.generate(), terms_version="   ")


# ---------- Indicadores comunitarios: umbral k-anonimato (RF-17, min 3 muestras) ----------


def test_indicadores_respetan_umbral_minimo_de_tres_muestras(api, act_as, make_user):
    def responder(neighborhood, mood, text=""):
        act_as(make_user())
        api.post(f"{BASE}/consent", json={})
        assert _survey(api, neighborhood=neighborhood, mood=mood, text=text).status_code == 201

    for mood in (2, 3):  # 2 muestras: por debajo del umbral, NO se publica
        responder("Villa Santana", mood)
    for mood, text in ((1, "no quiero vivir"), (4, ""), (5, "")):  # exactamente 3: se publica
        responder("Cuba", mood, text)

    r = api.get(f"{BASE}/indicators")
    assert r.status_code == 200
    assert r.json() == [
        {"neighborhood": "Cuba", "sample_count": 3, "average_mood": 3.33, "crisis_alerts": 1}
    ]


def test_lineas_de_ayuda_son_publicas(api):
    r = api.get(f"{BASE}/helplines")
    assert r.status_code == 200
    phones = {h["phone"] for h in r.json()["helplines"]}
    assert {"106", "123"} <= phones
