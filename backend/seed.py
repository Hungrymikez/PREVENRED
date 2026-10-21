import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sys

# Garantiza que el paquete 'prevenred' en 'src/' sea localizable al correr desde la raíz
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from motor.motor_asyncio import AsyncIOMotorClient

from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.main import INDEX_INITIALIZERS, ensure_async_indexes
from prevenred.shared.infrastructure.config import get_settings
from prevenred.shared.infrastructure.mongo import get_db


async def seed_database():
    settings = get_settings()
    print(f" Conectando a MongoDB: {settings.mongo_db_name}...")
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db_name]

    print(" Creando índices canónicos de la aplicación...")
    sync_db = get_db()
    for ensure in INDEX_INITIALIZERS:
        ensure(sync_db)

    print(" Creando índices de los contextos asíncronos (2dsphere, auditoría, bienestar)...")
    await ensure_async_indexes(db)

    print(" Insertando usuarios de prueba...")
    hasher = Argon2PasswordHasher()
    hashed_pwd = hasher.hash("Password2026*")

    now = datetime.now(UTC)
    users_seed = [
        {
            "_id": "000000000000000000000001",
            "email": "admin.diger@pereira.gov.co",
            "name": "Coordinador DIGER",
            "fullName": "Coordinador DIGER",
            "full_name": "Coordinador DIGER",
            "passwordHash": hashed_pwd,
            "password_hash": hashed_pwd,
            "roles": ["administrador"],
            "role": "administrador",
            "status": "ACTIVE",
            "is_active": True,
            "verified": True,
            "location": {"neighborhood": "Centro"},
            "neighborhood": "Centro",
            "consent": {
                "privacyNoticeVersion": "v1.0",
                "acceptedAt": now,
            },
            "privacy_notice_version": "v1.0",
            "terms_accepted_at": now,
            "security": {
                "failedLoginAttempts": 0,
                "lockedUntil": None,
            },
            "failed_login_attempts": 0,
            "locked_until": None,
            "createdAt": now,
            "created_at": now,
            "updatedAt": now,
        },
        {
            "_id": "000000000000000000000002",
            "email": "inspector.pereira@diger.gov.co",
            "name": "Ingeniero Evaluador",
            "fullName": "Ingeniero Evaluador",
            "full_name": "Ingeniero Evaluador",
            "passwordHash": hashed_pwd,
            "password_hash": hashed_pwd,
            "roles": ["inspector"],
            "role": "inspector",
            "status": "ACTIVE",
            "is_active": True,
            "verified": True,
            "location": {"neighborhood": "Cuba"},
            "neighborhood": "Cuba",
            "consent": {
                "privacyNoticeVersion": "v1.0",
                "acceptedAt": now,
            },
            "privacy_notice_version": "v1.0",
            "terms_accepted_at": now,
            "security": {
                "failedLoginAttempts": 0,
                "lockedUntil": None,
            },
            "failed_login_attempts": 0,
            "locked_until": None,
            "createdAt": now,
            "created_at": now,
            "updatedAt": now,
        },
        {
            "_id": "000000000000000000000003",
            "email": "ciudadano.ejemplo@gmail.com",
            "name": "Carlos Pérez",
            "fullName": "Carlos Pérez",
            "full_name": "Carlos Pérez",
            "passwordHash": hashed_pwd,
            "password_hash": hashed_pwd,
            "roles": ["ciudadano"],
            "role": "ciudadano",
            "status": "ACTIVE",
            "is_active": True,
            "verified": True,
            "location": {"neighborhood": "Boston"},
            "neighborhood": "Boston",
            "consent": {
                "privacyNoticeVersion": "v1.0",
                "acceptedAt": now,
            },
            "privacy_notice_version": "v1.0",
            "terms_accepted_at": now,
            "security": {
                "failedLoginAttempts": 0,
                "lockedUntil": None,
            },
            "failed_login_attempts": 0,
            "locked_until": None,
            "createdAt": now,
            "created_at": now,
            "updatedAt": now,
        },
    ]

    for user in users_seed:
        await db["users"].replace_one({"email": user["email"]}, user, upsert=True)

    print(" Insertando incidentes de muestra en Pereira...")
    incident_sample = {
        "_id": "000000000000000000000010",
        "case_number": "INC-20261019-BOST01",
        "caseId": "INC-20261019-BOST01",
        "type": "DESLIZAMIENTO",
        "incident_type": "DESLIZAMIENTO",
        "severity": "ALTA",
        "status": "REPORTADO",
        "description": "Deslizamiento preventivo en ladera cercana al Río Otún",
        "location": {"type": "Point", "coordinates": [-75.6961, 4.8133]},  # Sector Boston
        "reportedBy": "000000000000000000000003",
        "reported_by": "000000000000000000000003",
        "media_urls": [],
        "photos": [],
        "created_at": datetime.now(UTC),
        "createdAt": datetime.now(UTC),
        "history": [],
    }
    await db["incidents"].replace_one(
        {"case_number": incident_sample["case_number"]},
        incident_sample,
        upsert=True,
    )

    print(" Insertando materiales en SegundaVida Pereira...")
    material_sample = {
        "_id": "mat000000000000000000001",
        "title": "Ladrillos farol limpios sobrantes de obra",
        "description": "Disponibles 150 ladrillos en buen estado",
        "category": "CONSTRUCCION",
        "offer_type": "DONACION",
        "condition": "BUENO",
        "quantity": 150.0,
        "unit": "unidades",
        "price": 0.0,
        "location": {"type": "Point", "coordinates": [-75.6980, 4.8140]},
        "owner_id": "000000000000000000000003",
        "media_urls": [],
        "is_active": True,
        "created_at": datetime.now(UTC)
    }
    await db["materials"].replace_one({"_id": material_sample["_id"]}, material_sample, upsert=True)

    print("\n Base de datos poblada e inicializada con éxito en MongoDB Atlas.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
