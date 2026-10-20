"""Router FastAPI para los endpoints de voluntariado."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.identity.domain.user import User
from prevenred.identity.interface.dependencies import get_current_user
from prevenred.shared.infrastructure.mongo import get_database

from ..application.manage_volunteering import (
    AssignVolunteerCommand,
    ManageVolunteeringUseCase,
    RegisterVolunteerCommand,
)
from ..infrastructure.mongo_volunteer_repository import MongoVolunteerRepository
from .schemas import (
    AssignmentResponse,
    AssignVolunteerRequest,
    RegisterVolunteerRequest,
    VolunteerProfileResponse,
)

router = APIRouter(prefix="/volunteering", tags=["Volunteering & Mobilization"])


@router.post(
    "/register", response_model=VolunteerProfileResponse, status_code=status.HTTP_201_CREATED
)
async def register_volunteer(
    payload: RegisterVolunteerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> VolunteerProfileResponse:
    repo = MongoVolunteerRepository(db)
    use_case = ManageVolunteeringUseCase(repo)

    cmd = RegisterVolunteerCommand(
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        skills=payload.skills,
        longitude=payload.longitude,
        latitude=payload.latitude,
        user=current_user,
    )
    res = await use_case.register_volunteer(cmd)
    return VolunteerProfileResponse(
        id=res.id.value,
        user_id=res.user_id.value,
        full_name=res.full_name,
        phone_number=res.phone_number,
        skills=res.skills,
        is_available=res.is_available,
        longitude=res.longitude,
        latitude=res.latitude,
        created_at=res.created_at,
    )


@router.post("/assign", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_volunteer(
    payload: AssignVolunteerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> AssignmentResponse:
    repo = MongoVolunteerRepository(db)
    use_case = ManageVolunteeringUseCase(repo)

    cmd = AssignVolunteerCommand(
        volunteer_id=payload.volunteer_id,
        incident_id=payload.incident_id,
        task_description=payload.task_description,
        coordinator=current_user,
    )
    res = await use_case.assign_volunteer(cmd)
    return AssignmentResponse(
        id=res.id.value,
        volunteer_id=res.volunteer_id.value,
        incident_id=res.incident_id.value,
        task_description=res.task_description,
        status=res.status,
        assigned_by=res.assigned_by.value,
        created_at=res.created_at,
    )


@router.get("/assignments/my", response_model=list[AssignmentResponse])
async def list_my_assignments(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[AssignmentResponse]:
    repo = MongoVolunteerRepository(db)
    vol = await repo.get_by_user_id(current_user.id)
    if not vol:
        return []
    assignments = await repo.list_assignments_by_volunteer(vol.id)
    return [
        AssignmentResponse(
            id=a.id.value,
            volunteer_id=a.volunteer_id.value,
            incident_id=a.incident_id.value,
            task_description=a.task_description,
            status=a.status,
            assigned_by=a.assigned_by.value,
            created_at=a.created_at,
        )
        for a in assignments
    ]
