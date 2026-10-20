"""Router FastAPI para los endpoints de bienestar emocional y resiliencia comunitaria."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.identity.domain.user import User
from prevenred.identity.interface.dependencies import get_current_user
from prevenred.shared.infrastructure.mongo import get_database

from ..application.submit_survey import (
    GrantConsentCommand,
    SubmitSurveyCommand,
    WellbeingUseCase,
)
from ..infrastructure.mongo_wellbeing_repository import MongoWellbeingRepository
from .schemas import (
    CommunityIndicatorResponse,
    ConsentResponse,
    CrisisHelplineResponse,
    GrantConsentRequest,
    SubmitSurveyRequest,
    SurveySubmissionResponse,
)

router = APIRouter(prefix="/wellbeing", tags=["Wellbeing - Mente Resiliente"])


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_200_OK)
async def grant_consent(
    payload: GrantConsentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> ConsentResponse:
    repo = MongoWellbeingRepository(db)
    use_case = WellbeingUseCase(repo)

    res = await use_case.grant_consent(
        GrantConsentCommand(terms_version=payload.terms_version, user=current_user)
    )
    return ConsentResponse(
        user_id=res.user_id.value,
        terms_version=res.terms_version,
        consented_at=res.consented_at,
        is_revoked=res.is_revoked,
    )


@router.post(
    "/surveys", response_model=SurveySubmissionResponse, status_code=status.HTTP_201_CREATED
)
async def submit_survey(
    payload: SubmitSurveyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> SurveySubmissionResponse:
    repo = MongoWellbeingRepository(db)
    use_case = WellbeingUseCase(repo)

    res = await use_case.submit_survey(
        SubmitSurveyCommand(
            neighborhood=payload.neighborhood,
            mood_score=payload.mood_score,
            raw_text=payload.text,
            user=current_user,
        )
    )
    return SurveySubmissionResponse(
        survey_id=res.survey_id,
        neighborhood=res.neighborhood,
        mood_score=res.mood_score,
        crisis_detected=res.crisis_detected,
        crisis_support_message=res.crisis_support_message,
    )


@router.get("/indicators", response_model=list[CommunityIndicatorResponse])
async def get_indicators(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[CommunityIndicatorResponse]:
    repo = MongoWellbeingRepository(db)
    use_case = WellbeingUseCase(repo)

    indicators = await use_case.get_community_indicators()
    return [
        CommunityIndicatorResponse(
            neighborhood=item["neighborhood"],
            sample_count=item["sample_count"],
            average_mood=item["average_mood"],
            crisis_alerts=item["crisis_alerts"],
        )
        for item in indicators
    ]


@router.get("/helplines", response_model=CrisisHelplineResponse)
async def get_crisis_helplines() -> CrisisHelplineResponse:
    return CrisisHelplineResponse(
        city="Pereira, Risaralda",
        helplines=[
            {
                "name": "Línea de la Esperanza / Salud Mental",
                "phone": "106",
                "type": "Gratuita 24/7",
            },
            {
                "name": "Línea Amiga Pereira",
                "phone": "+573228615710",
                "type": "WhatsApp / Llamada",
            },
            {
                "name": "Emergencias Generales",
                "phone": "123",
                "type": "Policía / Cruz Roja / Bomberos",
            },
        ],
    )
