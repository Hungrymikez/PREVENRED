"""Entidades y tipos de dominio para gestión y asignación de voluntarios."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


class VolunteerSkill(StrEnum):
    PRIMEROS_AUXILIOS = "PRIMEROS_AUXILIOS"
    RESCATE = "RESCATE"
    LOGISTICA = "LOGISTICA"
    APOYO_PSICOLOGICO = "APOYO_PSICOLOGICO"
    CONDUCCION = "CONDUCCION"
    REMOCION_ESCOMBROS = "REMOCION_ESCOMBROS"
    OTRO = "OTRO"


class AssignmentStatus(StrEnum):
    ASIGNADO = "ASIGNADO"
    EN_CAMINO = "EN_CAMINO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"


@dataclass
class VolunteerProfile(Entity):
    user_id: EntityId
    full_name: str
    phone_number: str
    skills: list[VolunteerSkill]
    is_available: bool
    longitude: float
    latitude: float
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: EntityId,
        full_name: str,
        phone_number: str,
        skills: list[VolunteerSkill],
        longitude: float,
        latitude: float,
    ) -> "VolunteerProfile":
        if not full_name or len(full_name.strip()) < 3:
            raise DomainValidationError("El nombre completo debe tener al menos 3 caracteres.")
        if not skills:
            raise DomainValidationError("Debe indicar al menos una habilidad de voluntariado.")
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise DomainValidationError("Coordenadas geográficas inválidas.")

        return cls(
            id=EntityId.generate(),
            user_id=user_id,
            full_name=full_name.strip(),
            phone_number=phone_number.strip(),
            skills=skills,
            is_available=True,
            longitude=longitude,
            latitude=latitude,
            created_at=datetime.now(UTC),
        )


@dataclass
class VolunteerAssignment(Entity):
    volunteer_id: EntityId
    incident_id: EntityId
    task_description: str
    status: AssignmentStatus
    assigned_by: EntityId
    created_at: datetime

    @classmethod
    def create(
        cls,
        volunteer_id: EntityId,
        incident_id: EntityId,
        task_description: str,
        assigned_by: EntityId,
    ) -> "VolunteerAssignment":
        if not task_description or len(task_description.strip()) < 5:
            raise DomainValidationError(
                "La descripción de la tarea debe tener al menos 5 caracteres."
            )

        return cls(
            id=EntityId.generate(),
            volunteer_id=volunteer_id,
            incident_id=incident_id,
            task_description=task_description.strip(),
            status=AssignmentStatus.ASIGNADO,
            assigned_by=assigned_by,
            created_at=datetime.now(UTC),
        )
