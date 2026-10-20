"""
Repositorio de técnicos: colección `technicians` (CU-17, CU-18, CU-19, CU-44).

La búsqueda pública filtra por `verificationStatus: VERIFICADO` desde la propia
consulta (y no en memoria) para que el índice `specialties+verificationStatus`
sirva y un perfil pendiente nunca se filtre por error.
"""
from bson import ObjectId
from pymongo.database import Database

from prevenred.services.domain.entities import TechnicianProfile
from prevenred.services.domain.repositories import TechnicianRepository
from prevenred.shared.infrastructure.repository import (
    BaseMongoRepository,
    to_object_id,
    to_reference,
    utc_aware,
)

COLLECTION = "technicians"


def _to_entity(d: dict) -> TechnicianProfile:
    """Documento -> TechnicianProfile."""
    return TechnicianProfile(
        id=str(d["_id"]),
        user_id=str(d["userId"]),
        specialties=tuple(d.get("specialties") or ()),
        experience_years=int(d.get("experienceYears") or 0),
        verification_status=d.get("verificationStatus", "PENDIENTE"),
        portfolio=tuple(str(x) for x in d.get("portfolio") or ()),
        documents=tuple(str(x) for x in d.get("documents") or ()),
        availability=dict(d.get("availability") or {}),
        rating=float(d.get("rating") or 0),
        verified_by=str(d["verifiedBy"]) if d.get("verifiedBy") else None,
        verified_at=utc_aware(d.get("verifiedAt")),
        rejection_reason=d.get("rejectionReason"),
        created_at=utc_aware(d["createdAt"]),
        updated_at=utc_aware(d.get("updatedAt")),
    )


def _references(ids: tuple[str, ...]) -> list:
    """Ids -> lista de ObjectId válidos (descarta basura sin romper la escritura)."""
    return [ref for ref in (to_reference(i) for i in ids) if ref is not None]


class MongoTechnicianRepository(BaseMongoRepository[TechnicianProfile], TechnicianRepository):
    """TechnicianRepository sobre la colección `technicians`."""

    collection = COLLECTION

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._technicians = self._col

    def to_document(self, p: TechnicianProfile) -> dict:
        """Perfil -> documento completo."""
        return {
            "_id": ObjectId(p.id),
            "userId": to_reference(p.user_id),
            "specialties": list(p.specialties),
            "experienceYears": p.experience_years,
            "portfolio": _references(p.portfolio),
            "documents": _references(p.documents),
            "verificationStatus": p.verification_status,
            "availability": dict(p.availability),
            "rating": p.rating,
            "verifiedBy": to_reference(p.verified_by),
            "verifiedAt": p.verified_at,
            "rejectionReason": p.rejection_reason,
            "createdAt": p.created_at,
            "updatedAt": p.updated_at or p.created_at,
        }

    def to_entity(self, document: dict) -> TechnicianProfile:
        """Documento -> perfil."""
        return _to_entity(document)

    def updates(self, p: TechnicianProfile) -> dict:
        """Cambian documentos, disponibilidad y el resultado de la verificación."""
        return {
            "documents": _references(p.documents),
            "verificationStatus": p.verification_status,
            "availability": dict(p.availability),
            "rating": p.rating,
            "verifiedBy": to_reference(p.verified_by),
            "verifiedAt": p.verified_at,
            "rejectionReason": p.rejection_reason,
            "updatedAt": p.updated_at,
        }

    def get_by_user_id(self, user_id: str) -> TechnicianProfile | None:
        """Perfil del usuario (el índice único garantiza como máximo uno)."""
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = self._technicians.find_one({"userId": oid})
        return _to_entity(doc) if doc else None

    def search(
        self,
        *,
        specialty: str | None = None,
        verified_only: bool = True,
        limit: int = 50,
    ) -> list[TechnicianProfile]:
        """Técnicos por oficio; mejor valorados primero (CU-19)."""
        query: dict = {}
        if specialty is not None:
            query["specialties"] = specialty
        if verified_only:
            query["verificationStatus"] = "VERIFICADO"
        cursor = self._technicians.find(query).sort([("rating", -1), ("experienceYears", -1)])
        return [_to_entity(doc) for doc in cursor.limit(limit)]

    def list_verification_queue(self, *, limit: int = 100) -> list[TechnicianProfile]:
        """Pendientes de revisión, del más antiguo al más nuevo (CU-18)."""
        cursor = (
            self._technicians.find({"verificationStatus": "PENDIENTE"})
            .sort("createdAt", 1)
            .limit(limit)
        )
        return [_to_entity(doc) for doc in cursor]
