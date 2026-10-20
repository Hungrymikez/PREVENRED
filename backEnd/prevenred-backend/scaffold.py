"""
scaffold.py — Crea el esqueleto DDD de PrevenRed SIN gastar tokens de IA.

Uso:  python scaffold.py
Es idempotente: no pisa archivos que ya existen, así que puedes correrlo
de nuevo cuando agregues un contexto nuevo al diccionario CONTEXTS.

Cada contexto acotado (bounded context) corresponde a uno o varios módulos
M01..M14 del documento 04 y agrupa los casos de uso (CU) del documento 05.
"""
from pathlib import Path

# Capas de DDD dentro de cada contexto (de adentro hacia afuera):
#   domain          -> reglas de negocio puras (sin FastAPI, sin SQLAlchemy)
#   application     -> casos de uso (orquestan el dominio mediante "puertos")
#   infrastructure  -> detalles técnicos: BD, JWT, SMS, almacenamiento, etc.
#   interface       -> la puerta HTTP: routers y schemas de FastAPI
LAYERS = ["domain", "application", "infrastructure", "interface"]

# contexto -> (módulos del doc 04, casos de uso del doc 05)
# Las colecciones MongoDB de cada contexto están en COLLECTIONS (doc 09 + ajustes, ver docs/db/).
CONTEXTS = {
    "identity":      ("M01 Acceso, usuarios y roles",        "CU-01 CU-02 CU-03 CU-08"),
    "operating_mode":("M02 Modo operacional (Cotidiano/Emergencia)", "CU-04"),
    "audit":         ("M04 Auditoría",                        "CU-05 CU-09"),
    "notifications": ("M03 Notificaciones de crisis",         "CU-06 CU-07"),
    "marketplace":   ("M06 SegundaVida Pereira (+ reseñas)",  "CU-11 CU-12 CU-13 CU-14 CU-15 CU-16"),
    "services":      ("M07 OficiosYa Pereira",                "CU-17 CU-18 CU-19 CU-20 CU-21 CU-22"),
    "wellbeing":     ("M08 Mente Resiliente",                 "CU-23 CU-24 CU-25 CU-26 CU-27 CU-28"),
    "incidents":     ("M09 Reportes de emergencia", "CU-29 CU-30 CU-32 CU-39"),
    "fieldwork":     ("M05 Offline + M10 Censo e inspección + CU-38", "CU-34 CU-35 CU-36 CU-37 CU-38"),
    "geo":           ("M11 Mapa y ubicación",                 "CU-10 CU-40 CU-48"),
    "aid":           ("M12 Banco de ayudas y donaciones + CU-31 Solicitar ayuda (M09)", "CU-31 CU-33 CU-41 CU-42"),
    "volunteering":  ("M13 Bolsa de voluntariado",            "CU-43 CU-44"),
    "reporting":     ("M14 Dashboard municipal",              "CU-45 CU-46"),
    "media":         ("Archivos multimedia (transversal)",    "CU-47"),
}

COLLECTIONS = {
    'identity': 'users, roles, sessions, password_resets',
    'operating_mode': 'operational_modes',
    'audit': 'audit_logs',
    'notifications': 'notifications',
    'marketplace': 'materials, tools, reservations, transactions, reviews',
    'services': 'technicians, service_requests, quotes',
    'wellbeing': 'wellbeing_surveys, nlp_analysis, support_requests, wellbeing_consents, wellbeing_indicators',
    'incidents': 'incidents, incident_status_history',
    'fieldwork': 'properties, property_inspections',
    'geo': 'map_layers, catalogs',
    'aid': 'donations, aid_needs, donation_matches, aid_inventory',
    'volunteering': 'volunteers, assignments',
    'reporting': '(ninguna propia: agrega con aggregation pipelines)',
    'media': 'files'
}

ROOT = Path("src/prevenred")


def touch(path: Path, content: str = "") -> None:
    """Crea el archivo solo si no existe (nunca pisa trabajo previo)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def main() -> None:
    touch(ROOT / "__init__.py")

    # Núcleo compartido (shared kernel): lo que TODOS los contextos pueden usar.
    for sub in ["domain", "application", "infrastructure", "interface"]:
        touch(ROOT / "shared" / sub / "__init__.py")
    touch(ROOT / "shared" / "__init__.py")

    # Un paquete por contexto con sus 4 capas.
    for ctx, (modulo, cus) in CONTEXTS.items():
        touch(ROOT / ctx / "__init__.py")
        for layer in LAYERS:
            touch(ROOT / ctx / layer / "__init__.py")
        touch(
            ROOT / ctx / "README.md",
            f"# Contexto `{ctx}`\n\n- Módulo(s): {modulo}\n- Casos de uso: {cus}\n"
            f"- Colecciones MongoDB: {COLLECTIONS[ctx]}\n"
            f"- Fichas: `docs/cu/CU-xx.md` · Colecciones: `docs/db/<coleccion>.md`\n"
            f"- Estado: ⬜ pendiente\n",
        )

    for d in ["tests", "docs/cu", "docs/db"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("Estructura DDD lista en src/prevenred/")


if __name__ == "__main__":
    main()
