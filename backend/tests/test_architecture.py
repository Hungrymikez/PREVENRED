"""
Guardián de la arquitectura DDD. Corre con todo `pytest` y falla si alguien (persona o IA)
rompe las reglas de dependencias. Es la forma más barata de "no dañar nada".

Reglas:
  1. domain/       no importa librerías técnicas (FastAPI, PyMongo, Pydantic, JWT...).
  2. application/  no importa FastAPI ni PyMongo (usa puertos).
  3. Un contexto no importa el interior de otro. La "cara pública" de un contexto es solo:
       - domain/events.py          (eventos que publica)
       - application/ports.py      (puertos que otros pueden implementar o usar)
     Excepción: interface/dependencies.py y main.py son el cableado y pueden importar de todos.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "prevenred"
FORBIDDEN_IN_DOMAIN = {
    "fastapi",
    "starlette",
    "pymongo",
    "bson",
    "pydantic",
    "pydantic_settings",
    "jwt",
    "argon2",
    "sqlalchemy",
}
FORBIDDEN_IN_APPLICATION = {
    "fastapi",
    "starlette",
    "pymongo",
    "bson",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
}
PUBLIC_SURFACE = (
    "application.ports",
    "domain.events",
    "domain.user",
    "domain.role",
)


def _py_files():
    for path in SRC.rglob("*.py"):
        parts = path.relative_to(SRC).parts
        if len(parts) >= 2:  # ignora main.py y __init__ de la raíz
            yield path, parts


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.append(node.module)
    return names


def test_domain_y_application_no_importan_librerias_tecnicas():
    errors = []
    for path, parts in _py_files():
        layer = parts[1] if len(parts) > 2 else ""
        banned = {"domain": FORBIDDEN_IN_DOMAIN, "application": FORBIDDEN_IN_APPLICATION}.get(layer)
        if not banned:
            continue
        for module in _imports(path):
            if module.split(".")[0] in banned:
                errors.append(f"{path.relative_to(SRC)} importa '{module}' (prohibido en {layer}/)")
    assert not errors, "\n".join(errors)


def test_contextos_solo_se_ven_por_su_cara_publica():
    errors = []
    for path, parts in _py_files():
        ctx = parts[0]
        is_wiring = path.name in ("dependencies.py", "router.py")
        for module in _imports(path):
            segs = module.split(".")
            if segs[0] != "prevenred" or len(segs) < 3:
                continue
            other, inner = segs[1], ".".join(segs[2:])
            if other in (ctx, "shared") or is_wiring:
                continue
            if not inner.startswith(PUBLIC_SURFACE):
                errors.append(f"{path.relative_to(SRC)} importa '{module}' (interior de '{other}')")
    assert not errors, "\n".join(errors)
