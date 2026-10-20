"""
Auditoría de los cambios de rol y estado (CU-05, incluido en CU-08).

Colección `audit_logs` (contexto audit): solo se insertan documentos, nunca se
editan ni se borran. CU-08 E3 exige que, si esto falla, el cambio NO se aplique;
por eso el caso de uso llama a `record` ANTES de escribir el cambio y deja subir
la excepción.

`details` no lleva datos personales innecesarios (RN-05): solo el cambio
(rol anterior -> rol nuevo), nunca el nombre ni el correo.
"""
from pymongo.database import Database
from pymongo.errors import PyMongoError

from prevenred.identity.domain.repositories import RoleAssignmentAudit
from prevenred.shared.domain.errors import ConflictError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.infrastructure.repository import to_reference

COLLECTION = "audit_logs"


class MongoRoleAssignmentAudit(RoleAssignmentAudit):
    """RoleAssignmentAudit sobre la colección `audit_logs`."""

    def __init__(self, db: Database) -> None:
        self._logs = db[COLLECTION]

    def record(self, *, actor_id: str, action: str, target_id: str, details: dict) -> None:
        """Inserta el registro de auditoría.

        Si la base no puede registrar la auditoría se lanza ConflictError y el
        cambio no se aplica (E3): es preferible negar la operación a dejar un
        cambio de privilegios sin rastro.
        """
        try:
            self._logs.insert_one({
                "actorId": to_reference(actor_id),
                "action": action,
                "resource": "users",
                "resourceId": to_reference(target_id),
                "result": "SUCCESS",
                "createdAt": utcnow(),
                "details": dict(details),
            })
        except PyMongoError as exc:
            raise ConflictError(
                "No se pudo registrar la auditoría del cambio. La operación no se aplicó."
            ) from exc