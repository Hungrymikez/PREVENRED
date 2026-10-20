"""Repositorio de técnicos sobre la colección technicians."""
from bson import ObjectId
from pymongo.database import Database

from prevenred.services.domain.repositories import TechnicianRepository
from prevenred.services.domain.technician import Technician
from prevenred.shared.domain.errors import ValidationError

COLLECTION = "technicians"


def _oid(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValidationError("El identificador de usuario no es válido.")
    return ObjectId(value)


def _to_entity(doc: dict) -> Technician:
    return Technician(
        id=str(doc["_id"]),
        user_id=str(doc["userId"]),
        specialties=list(doc.get("specialties") or []),
        experience_years=int(doc.get("experienceYears") or 0),
        availability=str((doc.get("availability") or {}).get("label", "")),
        verification_status=doc.get("verificationStatus") or "PENDIENTE",
    )


class MongoTechnicianRepository(TechnicianRepository):
    """TechnicianRepository sobre MongoDB. Solo traduce; no decide reglas."""

    def __init__(self, db: Database) -> None:
        self._technicians = db[COLLECTION]

    def get_by_user_id(self, user_id: str) -> Technician | None:
        doc = self._technicians.find_one({"userId": _oid(user_id)})
        return _to_entity(doc) if doc else None

    def add(self, technician: Technician) -> None:
        self._technicians.insert_one({
            "_id": ObjectId(technician.id),
            "userId": _oid(technician.user_id),
            "specialties": technician.specialties,
            "experienceYears": technician.experience_years,
            "portfolio": [],
            "verificationStatus": technician.verification_status,
            "availability": {"label": technician.availability},
            "rating": None,
            "documents": [],
            "verifiedBy": None,
            "verifiedAt": None,
        })

    def update(self, technician: Technician) -> None:
        self._technicians.update_one(
            {"_id": ObjectId(technician.id)},
            {"$set": {
                "specialties": technician.specialties,
                "experienceYears": technician.experience_years,
                "verificationStatus": technician.verification_status,
                "availability": {"label": technician.availability},
            }},
        )
