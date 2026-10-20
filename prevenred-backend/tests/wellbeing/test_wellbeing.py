from collections import defaultdict
from typing import Any

import pytest

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.identity.domain.value_objects import Email
from prevenred.identity.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.shared.domain.errors import AuthorizationError, DomainValidationError
from prevenred.shared.domain.ids import EntityId
from prevenred.wellbeing.application.submit_survey import (
    GrantConsentCommand,
    SubmitSurveyCommand,
    WellbeingUseCase,
)
from prevenred.wellbeing.domain.consent import WellbeingConsent
from prevenred.wellbeing.domain.repositories import WellbeingRepository
from prevenred.wellbeing.domain.survey import WellbeingSurvey


class InMemoryWellbeingRepository(WellbeingRepository):
    def __init__(self) -> None:
        self.consents: dict[str, WellbeingConsent] = {}
        self.surveys: list[WellbeingSurvey] = []

    async def save_consent(self, consent: WellbeingConsent) -> None:
        uid = consent.user_id.value if hasattr(consent.user_id, "value") else str(consent.user_id)
        self.consents[uid] = consent

    async def get_consent_by_user_id(self, user_id: EntityId) -> WellbeingConsent | None:
        uid = user_id.value if hasattr(user_id, "value") else str(user_id)
        return self.consents.get(uid)

    async def save_survey(self, survey: WellbeingSurvey) -> None:
        self.surveys.append(survey)

    async def get_all_neighborhood_averages(self, min_samples: int = 3) -> list[dict[str, Any]]:
        grouped = defaultdict(list)
        for s in self.surveys:
            grouped[s.neighborhood].append(s)

        results = []
        for neigh, items in grouped.items():
            if len(items) >= min_samples:
                avg = sum(i.mood_score for i in items) / len(items)
                crisis = sum(1 for i in items if i.crisis_flag)
                results.append(
                    {
                        "neighborhood": neigh,
                        "sample_count": len(items),
                        "average_mood": round(avg, 2),
                        "crisis_alerts": crisis,
                    }
                )
        return results


@pytest.fixture
def test_user() -> User:
    return User.register(
        email=Email("vecina.bienestar@pereira.gov.co"),
        raw_password="SecurePass2026*",
        name="María Gómez",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def other_user() -> User:
    return User.register(
        email=Email("vecino.otro@pereira.gov.co"),
        raw_password="SecurePass2026*",
        name="Carlos Pérez",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


@pytest.mark.asyncio
async def test_survey_requires_prior_consent(test_user: User) -> None:
    repo = InMemoryWellbeingRepository()
    use_case = WellbeingUseCase(repo)

    cmd = SubmitSurveyCommand(
        neighborhood="Comuna Cuba",
        mood_score=3,
        raw_text="Me siento un poco preocupada por las lluvias.",
        user=test_user,
    )
    # Debe fallar porque no ha firmado consentimiento
    with pytest.raises(AuthorizationError, match="consentimiento informado"):
        await use_case.submit_survey(cmd)


@pytest.mark.asyncio
async def test_survey_revoked_consent_fails(test_user: User) -> None:
    repo = InMemoryWellbeingRepository()
    use_case = WellbeingUseCase(repo)

    consent = await use_case.grant_consent(
        GrantConsentCommand(terms_version="v1.0", user=test_user)
    )
    consent.is_revoked = True
    await repo.save_consent(consent)

    cmd = SubmitSurveyCommand(
        neighborhood="Comuna Cuba",
        mood_score=3,
        raw_text="Todo tranquilo en el sector.",
        user=test_user,
    )
    with pytest.raises(AuthorizationError, match="consentimiento informado"):
        await use_case.submit_survey(cmd)


@pytest.mark.asyncio
async def test_survey_sanitizes_pii_and_detects_crisis(test_user: User) -> None:
    repo = InMemoryWellbeingRepository()
    use_case = WellbeingUseCase(repo)

    # 1. Otorgar consentimiento
    await use_case.grant_consent(GrantConsentCommand(terms_version="v1.0", user=test_user))

    # 2. Enviar texto con datos sensibles (teléfono, cédula, correo) y mensaje de crisis
    cmd = SubmitSurveyCommand(
        neighborhood="Boston",
        mood_score=1,
        raw_text=(
            "Mi celular es 3109876543, cédula 1088123456 y correo maria@gmail.com. "
            "Siento desesperación total y no tengo salida."
        ),
        user=test_user,
    )
    result = await use_case.submit_survey(cmd)

    assert result.crisis_detected is True
    assert result.crisis_support_message is not None
    assert "106" in result.crisis_support_message

    saved_survey = repo.surveys[0]
    # Comprobar desidentificación (RNF-04)
    assert "3109876543" not in saved_survey.sanitized_text
    assert "1088123456" not in saved_survey.sanitized_text
    assert "maria@gmail.com" not in saved_survey.sanitized_text
    assert "[TEL_PROTEGIDO]" in saved_survey.sanitized_text
    assert "[ID_PROTEGIDO]" in saved_survey.sanitized_text
    assert "[CORREO_PROTEGIDO]" in saved_survey.sanitized_text


@pytest.mark.asyncio
async def test_community_indicators_k_anonymity(test_user: User, other_user: User) -> None:
    repo = InMemoryWellbeingRepository()
    use_case = WellbeingUseCase(repo)

    await use_case.grant_consent(GrantConsentCommand(terms_version="v1.0", user=test_user))
    await use_case.grant_consent(GrantConsentCommand(terms_version="v1.0", user=other_user))

    # 3 encuestas en Comuna Cuba (cumple k-anonymity min_samples=3)
    for score in [3, 4, 5]:
        await use_case.submit_survey(
            SubmitSurveyCommand(
                neighborhood="Cuba",
                mood_score=score,
                raw_text="Reporte comunitario",
                user=test_user,
            )
        )

    # Solo 2 encuestas en Villa Santana (< 3, debe quedar excluida por k-anonimato)
    for score in [2, 3]:
        await use_case.submit_survey(
            SubmitSurveyCommand(
                neighborhood="Villa Santana",
                mood_score=score,
                raw_text="Reporte del sector",
                user=other_user,
            )
        )

    indicators = await use_case.get_community_indicators()
    assert len(indicators) == 1
    assert indicators[0]["neighborhood"] == "Cuba"
    assert indicators[0]["sample_count"] == 3
    assert indicators[0]["average_mood"] == 4.0


@pytest.mark.asyncio
async def test_wellbeing_domain_validations(test_user: User) -> None:
    repo = InMemoryWellbeingRepository()
    use_case = WellbeingUseCase(repo)

    # Consentimiento con versión vacía
    with pytest.raises(DomainValidationError, match="Versión de términos requerida"):
        await use_case.grant_consent(GrantConsentCommand(terms_version="   ", user=test_user))

    await use_case.grant_consent(GrantConsentCommand(terms_version="v1.0", user=test_user))

    # Barrio muy corto (< 2 caracteres)
    with pytest.raises(DomainValidationError, match="al menos 2 caracteres"):
        await use_case.submit_survey(
            SubmitSurveyCommand(
                neighborhood="A",
                mood_score=3,
                raw_text="Reporte",
                user=test_user,
            )
        )

    # Escala de ánimo inválida (< 1 o > 5)
    with pytest.raises(DomainValidationError, match="entre 1 y 5"):
        await use_case.submit_survey(
            SubmitSurveyCommand(
                neighborhood="Centro",
                mood_score=6,
                raw_text="Reporte",
                user=test_user,
            )
        )

    with pytest.raises(DomainValidationError, match="entre 1 y 5"):
        await use_case.submit_survey(
            SubmitSurveyCommand(
                neighborhood="Centro",
                mood_score=0,
                raw_text="Reporte",
                user=test_user,
            )
        )


@pytest.mark.asyncio
async def test_survey_with_user_id_as_str(test_user: User) -> None:
    # Simula un usuario cuyo id es un str primitivo (por ejemplo cargado de BD)
    object.__setattr__(test_user, "id", "507f1f77bcf86cd799439011")
    assert isinstance(test_user.id, str)
    assert not hasattr(test_user.id, "value")

    repo = InMemoryWellbeingRepository()
    use_case = WellbeingUseCase(repo)

    # Consentimiento con user_id como str
    consent = await use_case.grant_consent(
        GrantConsentCommand(terms_version="v1.0", user=test_user)
    )
    assert consent.user_id == "507f1f77bcf86cd799439011"

    # Encuesta con user_id como str
    result = await use_case.submit_survey(
        SubmitSurveyCommand(
            neighborhood="Centro",
            mood_score=4,
            raw_text="Todo en orden en mi sector.",
            user=test_user,
        )
    )
    assert result.neighborhood == "Centro"
    assert result.mood_score == 4
    assert result.crisis_detected is False
