"""
Índices de las colecciones de identity. Se crean al arrancar la app (idempotente).
En MongoDB la unicidad del correo y del `jti` las garantiza el ÍNDICE, no solo el código.
Los índices TTL hacen que Mongo borre sesiones y enlaces vencidos sin código extra.

Los nombres de colección NO se escriben aquí: se importan del repositorio que es
dueño de cada una, así existe una sola constante por colección.
"""
from pymongo import ASCENDING
from pymongo.database import Database

from prevenred.identity.infrastructure.mongo_auth_repository import (
    PASSWORD_RESETS,
    SESSIONS,
)
from prevenred.identity.infrastructure.mongo_mfa_challenge_repository import (
    COLLECTION as MFA_CHALLENGES,
)

#: `users` es de este contexto y lo escribe MongoUserRepository.
USERS = "users"


def ensure_indexes(db: Database) -> None:
    """Crea los índices de users, sessions y password_resets si no existen (se puede repetir)."""
    db[USERS].create_index("email", unique=True, name="uq_users_email")
    db[USERS].create_index("status", name="ix_users_status")

    # CU-02 A4: un `jti` identifica un único token emitido. El TTL borra la sesión
    # cuando vence: un token vencido no necesita seguimiento manual.
    db[SESSIONS].create_index("jti", unique=True, name="uq_sessions_jti")
    db[SESSIONS].create_index("userId", name="ix_sessions_user")
    db[SESSIONS].create_index(
        "expiresAt", name="ttl_sessions_expires", expireAfterSeconds=0
    )

    # CU-02 A2: se busca por hash del token; los enlaces vencidos se borran solos.
    db[PASSWORD_RESETS].create_index(
        "tokenHash", unique=True, name="uq_password_resets_hash"
    )
    db[PASSWORD_RESETS].create_index(
        "userId", name="ix_password_resets_user"
    )
    db[PASSWORD_RESETS].create_index(
        "expiresAt", name="ttl_password_resets_expires", expireAfterSeconds=0
    )
    # "El más reciente primero" al listar/auditar.
    db[PASSWORD_RESETS].create_index(
        [("userId", ASCENDING), ("createdAt", ASCENDING)],
        name="ix_password_resets_user_created",
    )

    # CU-03: se busca el desafío ABIERTO de una operación por (userId, purpose,
    # status) y el último VERIFICADO por (userId, purpose, status, verifiedAt).
    # Un solo índice compuesto sirve a ambas consultas; el TTL borra los vencidos.
    db[MFA_CHALLENGES].create_index(
        [("userId", ASCENDING), ("purpose", ASCENDING), ("status", ASCENDING),
         ("verifiedAt", ASCENDING)],
        name="ix_mfa_challenges_user_purpose_status",
    )
    db[MFA_CHALLENGES].create_index(
        "expiresAt", name="ttl_mfa_challenges_expires", expireAfterSeconds=0
    )

    # CU-08 E1: contar Administradores activos es una consulta crítica (nunca
    # puede quedar la plataforma sin uno); el índice de `status` ya ayuda, y este
    # evita recorrer todas las cuentas al suspender o cambiar un rol.
    db[USERS].create_index(
        [("roles", ASCENDING), ("status", ASCENDING)], name="ix_users_role_status"
    )

    # RN-05: se agrupa por barrio/comuna para mapas de calor y reportes; hoy vive
    # en el campo raíz `neighborhood` (antes dentro de `location`).
    db[USERS].create_index("neighborhood", name="ix_users_neighborhood")

    # CU-08: la auditoría se consulta por actor y por recurso afectado.
    db["audit_logs"].create_index(
        [("actorId", ASCENDING), ("createdAt", ASCENDING)], name="ix_audit_actor_created"
    )
    db["audit_logs"].create_index(
        [("resource", ASCENDING), ("resourceId", ASCENDING), ("createdAt", ASCENDING)],
        name="ix_audit_resource",
    )

