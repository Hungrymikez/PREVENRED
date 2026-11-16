"""Semilla de demo para SegundaVida (materials) y OficiosYa (technicians).

Las pantallas buscan por cercanía ($nearSphere). Si las colecciones están vacías,
la API responde 200 con [] y el frontend muestra «sin resultados».

Uso, desde la carpeta backend:

    py -3.13 scripts/seed_demo_marketplace.py

Es idempotente: usa _id fijos y hace upsert.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pymongo import GEOSPHERE, MongoClient

from prevenred.shared.infrastructure.config import get_settings

OWNER_ID = "65f1a2b3c4d5e6f7a8b90001"
ADMIN_ID = "8eae35f530a2ff004c6cc3e6"
NOW = datetime.now(UTC)

# Puntos alrededor del centro de Pereira.
MATERIALS = [
    {
        "_id": "a10000000000000000000001",
        "title": "Taladro percutor Bosch",
        "description": "Taladro en buen estado, con maletín y brocas. Ideal para trabajos ligeros.",
        "category": "HERRAMIENTAS",
        "offer_type": "ALQUILER",
        "condition": "BUENO",
        "quantity": 1,
        "unit": "unidades",
        "price": 25000,
        "location": {"type": "Point", "coordinates": [-75.6961, 4.8133]},
        "owner_id": OWNER_ID,
        "owner_name": "Carlos M.",
        "media_urls": [],
        "is_active": True,
        "created_at": NOW,
    },
    {
        "_id": "a10000000000000000000002",
        "title": "Ladrillos refractarios",
        "description": "Lote de ladrillos sobrantes de una remodelación. Retiro en Cuba.",
        "category": "CONSTRUCCION",
        "offer_type": "VENTA",
        "condition": "USADO",
        "quantity": 80,
        "unit": "unidades",
        "price": 400,
        "location": {"type": "Point", "coordinates": [-75.7050, 4.8080]},
        "owner_id": OWNER_ID,
        "owner_name": "María L.",
        "media_urls": [],
        "is_active": True,
        "created_at": NOW,
    },
    {
        "_id": "a10000000000000000000003",
        "title": "Tubería PVC 1/2\"",
        "description": "Donación de tubos PVC nuevos, sin usar. Preferiblemente en Centro.",
        "category": "PLOMERIA",
        "offer_type": "DONACION",
        "condition": "NUEVO",
        "quantity": 12,
        "unit": "metros",
        "price": 0,
        "location": {"type": "Point", "coordinates": [-75.6900, 4.8200]},
        "owner_id": OWNER_ID,
        "owner_name": "Andrés P.",
        "media_urls": [],
        "is_active": True,
        "created_at": NOW,
    },
    {
        "_id": "a10000000000000000000004",
        "title": "Tablero de madera pino",
        "description": "Tablones de 2 m para estantería o refuerzo ligero.",
        "category": "MADERA",
        "offer_type": "VENTA",
        "condition": "BUENO",
        "quantity": 6,
        "unit": "unidades",
        "price": 18000,
        "location": {"type": "Point", "coordinates": [-75.7005, 4.8155]},
        "owner_id": OWNER_ID,
        "owner_name": "Laura G.",
        "media_urls": [],
        "is_active": True,
        "created_at": NOW,
    },
]

# PrevenRED2 aún tiene el índice único legado `userId` (camelCase) además de `user_id`.
# Escribimos ambos para no chocar con E11000 cuando userId queda null.
TECHNICIANS = [
    {
        "_id": "b20000000000000000000001",
        "user_id": "b20000000000000000000011",
        "userId": "b20000000000000000000011",
        "full_name": "Julián Restrepo",
        "phone_number": "+573001112233",
        "specialties": ["PLOMERIA", "PINTURA"],
        "experience_years": 8,
        "bio": "Plomero certificado. Atención a fugas, sanitarios e instalaciones nuevas.",
        "verification_status": "VERIFICADO",
        "rating_average": 4.8,
        "reviews_count": 23,
        "location": {"type": "Point", "coordinates": [-75.6940, 4.8140]},
        "created_at": NOW,
        "verified_by": ADMIN_ID,
    },
    {
        "_id": "b20000000000000000000002",
        "user_id": "b20000000000000000000012",
        "userId": "b20000000000000000000012",
        "full_name": "Diana Quintero",
        "phone_number": "+573004445566",
        "specialties": ["ELECTRICIDAD"],
        "experience_years": 5,
        "bio": "Electricista residencial. Tableros, tomas, iluminación LED.",
        "verification_status": "VERIFICADO",
        "rating_average": 4.6,
        "reviews_count": 14,
        "location": {"type": "Point", "coordinates": [-75.7020, 4.8100]},
        "created_at": NOW,
        "verified_by": ADMIN_ID,
    },
    {
        "_id": "b20000000000000000000003",
        "user_id": "b20000000000000000000013",
        "userId": "b20000000000000000000013",
        "full_name": "Héctor Salazar",
        "phone_number": "+573007778899",
        "specialties": ["CONSTRUCCION", "CARPINTERIA"],
        "experience_years": 12,
        "bio": "Maestro de obra y carpintero. Reparaciones post-sismo y refuerzos.",
        "verification_status": "VERIFICADO",
        "rating_average": 4.9,
        "reviews_count": 41,
        "location": {"type": "Point", "coordinates": [-75.6885, 4.8180]},
        "created_at": NOW,
        "verified_by": ADMIN_ID,
    },
]


def _ensure_admin_password(db) -> None:
    """Restablece la clave del admin de desarrollo para el equipo."""
    from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher

    email = "admin.dev@prevenred.co"
    password = "AdminPrevenred2026*"
    hashed = Argon2PasswordHasher().hash(password)
    result = db["users"].update_one(
        {"email": email},
        {"$set": {"password_hash": hashed, "status": "ACTIVO"}},
    )
    if result.matched_count:
        print(f"Admin listo: {email} / {password}")
    else:
        print(f"No se encontró {email}; crea el admin antes o ignora este aviso.")


def main() -> None:
    settings = get_settings()
    client = MongoClient(settings.mongo_uri, tz_aware=True)
    db = client[settings.mongo_db_name]

    materials = db["materials"]
    technicians = db["technicians"]
    materials.create_index([("location", GEOSPHERE)])
    technicians.create_index([("location", GEOSPHERE)])
    technicians.create_index("user_id", unique=True)

    for doc in MATERIALS:
        materials.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    for doc in TECHNICIANS:
        technicians.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    _ensure_admin_password(db)

    print(f"materials: {materials.count_documents({})} documentos")
    print(
        "technicians (VERIFICADO): "
        f"{technicians.count_documents({'verification_status': 'VERIFICADO'})} documentos"
    )
    print("Listo. Recarga SegundaVida y OficiosYa (OficiosYa exige sesión iniciada).")


if __name__ == "__main__":
    main()
