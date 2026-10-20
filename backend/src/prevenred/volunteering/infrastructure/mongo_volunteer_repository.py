"""Repositorio de voluntarios sobre la colección volunteers."""
from bson import ObjectId
from pymongo.database import Database

from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.volunteering.domain.repositories import VolunteerRepository
from prevenred.volunteering.domain.volunteer import Volunteer

COLLECTION = "volunteers"


def _oid(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValidationError("El identificador de usuario no es válido.")
    return ObjectId(value)


def _to_entity(doc: dict) -> Volunteer:
    location = doc.get("location") or {}
    coordinates = location.get("coordinates") or [0, 0]
    return Volunteer(
        id=str(doc["_id"]),
        user_id=str(doc["userId"]),
        skills=list(doc.get("skills") or []),
        availability=str((doc.get("availability") or {}).get("label", "")),
        longitude=float(coordinates[0]),
        latitude=float(coordinates[1]),
        authorization_status=doc.get("authorizationStatus") or "PENDIENTE",
    )


class MongoVolunteerRepository(VolunteerRepository):
    """VolunteerRepository sobre MongoDB. Solo traduce; no decide reglas."""

    def __init__(self, db: Database) -> None:
        self._volunteers = db[COLLECTION]

    def get_by_user_id(self, user_id: str) -> Volunteer | None:
        doc = self._volunteers.find_one({"userId": _oid(user_id)})
        return _to_entity(doc) if doc else None

    def add(self, volunteer: Volunteer) -> None:
        self._volunteers.insert_one({
            "_id": ObjectId(volunteer.id),
            "userId": _oid(volunteer.user_id),
            "skills": volunteer.skills,
            "availability": {"label": volunteer.availability},
            "location": {
                "type": "Point",
                "coordinates": [volunteer.longitude, volunteer.latitude],
            },
            "certifications": [],
            "authorizationStatus": volunteer.authorization_status,
            "createdAt": utcnow(),
        })

    def update(self, volunteer: Volunteer) -> None:
        self._volunteers.update_one(
            {"_id": ObjectId(volunteer.id)},
            {"$set": {
                "skills": volunteer.skills,
                "availability": {"label": volunteer.availability},
                "location": {
                    "type": "Point",
                    "coordinates": [volunteer.longitude, volunteer.latitude],
                },
                "authorizationStatus": volunteer.authorization_status,
            }},
        )
