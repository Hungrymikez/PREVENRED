"""
export_mongo_schema.py — Exporta la ESTRUCTURA de una base MongoDB. SOLO LECTURA.

Qué guarda en el archivo de salida:
  - nombres de colecciones y cantidad aproximada de documentos
  - los validadores $jsonSchema (las reglas que Mongo aplica al guardar)
  - los índices
  - los campos que aparecen en una muestra de documentos, con su TIPO (string, date, objectId...)

Qué NO guarda: valores de los datos (ni correos, ni nombres, ni contraseñas) ni la cadena de
conexión. Solo lee: no inserta, no modifica y no borra nada.

Uso:
    pip install "pymongo[srv]"
    python tools/export_mongo_schema.py
(te pide la cadena de conexión sin mostrarla en pantalla y el nombre de la base)
"""
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from getpass import getpass

from bson import json_util

SAMPLE_SIZE = 25  # documentos que se miran por colección


def type_name(value) -> str:
    """Nombre legible del tipo de un valor (sin revelar el valor)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    for py_type, name in ((int, "int"), (float, "double"), (str, "string"),
                          (datetime, "date"), (dict, "object"), (list, "array")):
        if isinstance(value, py_type):
            return name
    return type(value).__name__  # ObjectId, Decimal128, Binary...


def walk(doc: dict, prefix: str, acc: dict) -> None:
    """Recorre un documento y anota el tipo de cada campo (incluye objetos y arreglos anidados)."""
    for key, value in doc.items():
        path = f"{prefix}.{key}" if prefix else key
        acc[path][type_name(value)] += 1
        if isinstance(value, dict):
            walk(value, path, acc)
        elif isinstance(value, list):
            for item in value[:5]:
                acc[path + "[]"][type_name(item)] += 1
                if isinstance(item, dict):
                    walk(item, path + "[]", acc)


def export_structure(db) -> dict:
    options = {}
    try:
        for info in db.list_collections():
            options[info["name"]] = info.get("options", {})
    except Exception:  # algunos usuarios no pueden listar opciones
        pass

    result = {}
    for name in sorted(db.list_collection_names()):
        if name.startswith("system."):
            continue
        coll = db[name]
        fields: dict = defaultdict(Counter)
        sampled = 0
        for doc in coll.find().limit(SAMPLE_SIZE):
            sampled += 1
            walk(doc, "", fields)
        opts = options.get(name, {})
        result[name] = {
            "approxDocuments": coll.estimated_document_count(),
            "validator": opts.get("validator"),
            "validationLevel": opts.get("validationLevel"),
            "validationAction": opts.get("validationAction"),
            "indexes": [
                {"name": idx, **{k: v for k, v in info.items() if k != "v"}}
                for idx, info in coll.index_information().items()
            ],
            "sampledDocuments": sampled,
            "fieldsSeen": {p: dict(c) for p, c in sorted(fields.items())},
        }
    return result


def main() -> None:
    from pymongo import MongoClient

    uri = os.getenv("MONGO_URI") or getpass("Cadena de conexión (no se muestra al escribir): ")
    db_name = input("Nombre de la base [prevenred2]: ").strip() or "prevenred2"
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    data = {
        "database": db_name,
        "exportedAt": datetime.now(UTC).isoformat(),
        "collections": export_structure(client[db_name]),
    }
    out = f"estructura_{db_name}.json"
    with open(out, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(data, indent=2, ensure_ascii=False))
    print(f"Listo: {len(data['collections'])} colecciones exportadas a {out}")
    print("Revisa el archivo antes de compartirlo: no contiene datos ni la conexión.")


if __name__ == "__main__":
    main()
