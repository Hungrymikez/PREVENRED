"""
audit_kit.py — Auditoría MECÁNICA del kit (no usa IA, no gasta tokens).

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python scripts/audit_kit.py            # imprime el informe
    python scripts/audit_kit.py --no-tests # omite ruff/pytest (más rápido)

Salida: una línea por verificación con [OK], [FALLA], [AVISO] o [OMITIDO], y un resumen.
Código de salida 1 si hay alguna FALLA. No modifica nada del proyecto (usa carpetas temporales).
Las comprobaciones de juicio (seguridad, claridad, utilidad) las hace Cline con docs/AUDITORIA_KIT.md.
"""
import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT.parent / "docs"
SRC = ROOT / "src" / "prevenred"
RESULTS: list[tuple[str, str, str]] = []  # (estado, id, detalle)


def check(state: str, ident: str, detail: str = "") -> None:
    RESULTS.append((state, ident, detail))


def run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------- 1. estructura
def check_structure() -> None:
    required = [
        "scaffold.py", "requirements.txt", "requirements-dev.txt", "ruff.toml",
        "pytest.ini", ".env.example", "compose.yaml", "scripts/gen_db_docs.py",
        "src/prevenred/main.py", "tests/conftest.py", "tests/test_architecture.py",
    ]
    missing = [f for f in required if not (ROOT / f).exists()]
    doc_required = [
        "GUIA_PODMAN.md", "AUDITORIA_KIT.md", "09_rectificacion_bd_mongodb.md",
        "reglas_transversales.md", "indice_cu.md",
    ]
    missing += [f"docs/{name}" for name in doc_required if not (DOCS / name).exists()]
    if not (DOCS / "PLAN_BACKEND.md").exists():
        missing.append("docs/PLAN_BACKEND.md")
    check("FALLA" if missing else "OK", "E1 archivos esenciales", f"faltan: {missing}" if missing else f"{len(required)} presentes")


# ---------------------------------------------------------------- 2. fichas de casos de uso
def check_cu_cards() -> None:
    bad, ok = [], 0
    for n in range(1, 49):
        p = DOCS / "cu" / f"CU-{n:02d}.md"
        if not p.exists() or not read(p).lstrip().startswith(f"### CU-{n:02d}"):
            bad.append(f"CU-{n:02d}")
        else:
            ok += 1
    check("FALLA" if bad else "OK", "C1 48 fichas de casos de uso", f"problemas: {bad}" if bad else "48/48 válidas")
    sizes = [(DOCS / "cu" / f"CU-{n:02d}.md").stat().st_size for n in range(1, 49) if (DOCS / "cu" / f"CU-{n:02d}.md").exists()]
    if sizes:
        check("OK" if max(sizes) < 8000 else "AVISO", "C2 tamaño de fichas CU", f"máx {max(sizes)} bytes, prom {sum(sizes)//len(sizes)}")


# ---------------------------------------------------------------- 3. contextos: CU y colecciones
def _readme_field(path: Path, label: str) -> str:
    for line in read(path).splitlines():
        if line.startswith(f"- {label}"):
            return line.split(":", 1)[1]
    return ""


def check_context_mapping() -> None:
    contexts = [p for p in SRC.iterdir() if p.is_dir() and p.name != "shared" and not p.name.startswith("__")]
    cu_owner: dict[str, list[str]] = {}
    col_owner: dict[str, list[str]] = {}
    for ctx in contexts:
        readme = ctx / "README.md"
        if not readme.exists():
            check("FALLA", f"M0 README de {ctx.name}", "no existe")
            continue
        for cu in re.findall(r"CU-\d\d", _readme_field(readme, "Casos de uso")):
            cu_owner.setdefault(cu, []).append(ctx.name)
        for col in re.findall(r"[a-z_]+", _readme_field(readme, "Colecciones MongoDB")):
            if col not in ("ninguna", "propia", "agrega", "con", "aggregation", "pipelines"):
                col_owner.setdefault(col, []).append(ctx.name)
    all_cu = {f"CU-{n:02d}" for n in range(1, 49)}
    missing = sorted(all_cu - set(cu_owner))
    dup = {k: v for k, v in cu_owner.items() if len(v) > 1}
    check("FALLA" if missing or dup else "OK", "M1 cada CU en un solo contexto", f"sin contexto: {missing}; repetidos: {dup}" if missing or dup else "48 CU, cada uno en 1 contexto")

    db_cols = {p.stem for p in (DOCS / "db").glob("*.md") if p.stem != "_indice"}
    shared_cols = {"counters"}
    unowned = sorted(db_cols - set(col_owner) - shared_cols)
    multi = {k: v for k, v in col_owner.items() if len(v) > 1}
    unknown = sorted(set(col_owner) - db_cols)
    state = "FALLA" if unowned or multi or unknown else "OK"
    check(state, "M2 cada colección en un solo contexto", f"sin dueño: {unowned}; repetidas: {multi}; sin ficha: {unknown}" if state == "FALLA" else f"{len(db_cols)} colecciones, 1 dueño cada una")


# ---------------------------------------------------------------- 4. plan cubre CU 03..48
def check_plan_phases() -> None:
    plan = read(DOCS / "PLAN_BACKEND.md")
    m = re.search(r"## 7\. Fases(.*?)## 8\.", plan, re.S)
    if not m:
        check("FALLA", "P1 sección de fases en el plan", "no se encontró")
        return
    section = m.group(1)
    covered: set[int] = set()
    for a, b in re.findall(r"CU-(\d+) a CU-(\d+)", section):
        covered |= set(range(int(a), int(b) + 1))
    covered |= {int(x) for x in re.findall(r"CU-(\d+)", section)}
    missing = [f"CU-{n:02d}" for n in range(3, 49) if n not in covered]
    check("FALLA" if missing else "OK", "P1 el plan cubre CU-03..CU-48", f"faltan: {missing}" if missing else "46/46 cubiertos")
    # el hito de 22 críticos
    index = read(DOCS / "indice_cu.md")
    critical = {int(n) for n, pr in re.findall(r"\*\*CU-(\d+)\*\* \|[^\n]*\| (Crítica|Alta|Media) \|", index) if pr == "Crítica"}
    phases_1_5 = re.search(r"\| 1 \|(.*?)\*\*Hito", section, re.S)
    if phases_1_5:
        cov15 = {int(x) for x in re.findall(r"CU-(\d+)", phases_1_5.group(1))} | {1, 2}
        miss_crit = sorted(critical - cov15)
        check("FALLA" if miss_crit else "OK", "P2 Fases 1-5 incluyen todos los CU Críticos", f"críticos fuera de fases 1-5: {miss_crit}" if miss_crit else f"{len(critical)} críticos dentro de fases 1-5")
    else:
        check("AVISO", "P2 hito de Críticos", "no se pudo localizar el hito en el plan")


# ---------------------------------------------------------------- 5. residuos de SQL
def check_sql_leftovers() -> None:
    pat_i = re.compile(r"sqlalchemy|alembic|postgres|sqlite|unitofwork|psycopg", re.I)
    pat_uuid = re.compile(r"\bUUID\b")  # en mayúsculas: uuid4 para nombres de pruebas es válido

    def pat_search(line: str) -> bool:
        return bool(pat_i.search(line) or pat_uuid.search(line))
    hits = []
    for base in (SRC, ROOT / "tests"):
        for p in base.rglob("*.py"):
            if p.name == "test_architecture.py":
                continue  # menciona sqlalchemy como librería prohibida a propósito
            for i, line in enumerate(read(p).splitlines(), 1):
                if pat_search(line):
                    hits.append(f"{p.relative_to(ROOT)}:{i}")
    for f in ("requirements.txt", "requirements-dev.txt", ".env.example"):
        for i, line in enumerate(read(ROOT / f).splitlines(), 1):
            if pat_search(line):
                hits.append(f"{f}:{i}")
    check("FALLA" if hits else "OK", "S1 sin restos de SQL/UUID en código", f"{hits[:5]}" if hits else "limpio")


# ---------------------------------------------------------------- 6. comentarios (docstrings)
def check_docstrings() -> None:
    no_module_doc, total_pub, with_doc = [], 0, 0
    for p in SRC.rglob("*.py"):
        text = read(p)
        if not text.strip():
            continue
        tree = ast.parse(text)
        if ast.get_docstring(tree) is None:
            no_module_doc.append(str(p.relative_to(ROOT)))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and not node.name.startswith("_"):
                total_pub += 1
                with_doc += ast.get_docstring(node) is not None
    check("FALLA" if no_module_doc else "OK", "D1 todo archivo con docstring de módulo", f"sin docstring: {no_module_doc[:5]}" if no_module_doc else "100% de los archivos con código")
    ratio = with_doc / total_pub if total_pub else 1
    check("OK" if ratio >= 0.5 else "AVISO", "D2 clases/funciones públicas con docstring", f"{with_doc}/{total_pub} ({ratio:.0%}). Los métodos triviales pueden ir sin docstring")


# ---------------------------------------------------------------- 7. reglas para Cline
def check_cline_rules() -> None:
    rules = ROOT / ".clinerules"
    if not rules.exists():
        check("OMITIDO", "R1 .clinerules", "archivo retirado del repositorio")
        return
    size = rules.stat().st_size
    check("OK" if size <= 4000 else "AVISO", "R1 tamaño de .clinerules (se envía en cada llamada)", f"{size} bytes")
    text = read(rules)
    needed = ["español", "domain", "application", "infrastructure", "interface", "MongoDB", "docs/db", "No dañar"]
    miss = [w for w in needed if w not in text]
    check("FALLA" if miss else "OK", "R2 .clinerules cubre arquitectura, Mongo y protección", f"faltan términos: {miss}" if miss else "completo")


# ---------------------------------------------------------------- 8. seguridad estática básica (identity)
def check_security_static() -> None:
    schemas = read(SRC / "auth" / "interface" / "schemas.py")
    resp = re.search(r"class UserResponse\(.*?(?=\nclass |\Z)", schemas, re.S)
    leak = bool(resp and re.search(r"password|hash", resp.group(0), re.I))
    check("FALLA" if leak else "OK", "X1 las respuestas no exponen la contraseña ni su hash", "UserResponse expone un campo de contraseña" if leak else "correcto")
    cfg = read(SRC / "shared" / "infrastructure" / "config.py")
    default_secret = "cambia-esto" in cfg
    guarded = "cambia-esto" in "".join(read(p) for p in SRC.rglob("main.py")) or "jwt_secret" in read(SRC / "main.py")
    if default_secret and not guarded:
        check("AVISO", "X2 secreto JWT por defecto sin verificación al arrancar", "la app arrancaría en producción con el secreto de ejemplo")
    else:
        check("OK", "X2 secreto JWT", "sin secreto por defecto o verificado al arrancar")
    login = read(SRC / "auth" / "application" / "login_user.py")
    check("OK" if "is_administrative" in login else "FALLA", "X3 administradores sin MFA no obtienen sesión", "falla cerrada presente" if "is_administrative" in login else "no se encontró el bloqueo")
    user_dep = read(SRC / "auth" / "interface" / "dependencies.py")
    check("AVISO" if "is_active" not in user_dep else "OK", "X4 el token no revalida si el usuario sigue activo", "un usuario suspendido con token vigente seguiría autenticado hasta que venza (se cierra con sessions/CU-08)")


# ---------------------------------------------------------------- 9. docs/db en sincronía con su generador
def check_db_docs_in_sync() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "gen_db_docs.py", t / "scripts" / "gen_db_docs.py")
        r = subprocess.run([sys.executable, "scripts/gen_db_docs.py"], cwd=t, capture_output=True, text=True)
        if r.returncode != 0:
            check("FALLA", "G1 el generador de fichas de colecciones corre", r.stderr[-200:])
            return
        diffs = []
        for gen in (t / "docs" / "db").glob("*.md"):
            cur = DOCS / "db" / gen.name
            if not cur.exists() or read(cur) != read(gen):
                diffs.append(gen.name)
        extra = [p.name for p in (DOCS / "db").glob("*.md") if not (t / "docs" / "db" / p.name).exists()]
        check("FALLA" if diffs or extra else "OK", "G2 docs/db coincide con tools/gen_db_docs.py", f"distintos: {diffs}; sobrantes: {extra}" if diffs or extra else f"{len(list((t/'docs'/'db').glob('*.md')))-1} fichas + índice en sincronía")


# ---------------------------------------------------------------- 10. main.py registra lo que debe
def check_main_wiring() -> None:
    main = read(SRC / "main.py")
    ok = all(s in main for s in ("identity_router", "include_router", "INDEX_INITIALIZERS", "EVENT_SUBSCRIBERS", "register_error_handlers"))
    check("OK" if ok else "FALLA", "W1 main.py registra router, índices, eventos y errores", "completo" if ok else "falta algún registro")
    idx = read(SRC / "auth" / "infrastructure" / "indexes.py")
    check("OK" if 'unique=True' in idx and '"email"' in idx else "FALLA", "W2 índice único de correo", "presente" if 'unique=True' in idx else "falta")


# ---------------------------------------------------------------- 11. ruff + pytest + guardián
def check_tests() -> None:
    py = sys.executable
    r = run([py, "-m", "ruff", "check", "src", "tests"])
    if "No module named ruff" in r.stderr:
        check("OMITIDO", "T1 ruff", "ruff no instalado (pip install -r requirements-dev.txt)")
    else:
        check("OK" if r.returncode == 0 else "FALLA", "T1 ruff sin errores", "limpio" if r.returncode == 0 else r.stdout[-300:])
    r = run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    check("OK" if r.returncode == 0 else "FALLA", "T2 pytest", tail)
    # el guardián debe DETECTAR una violación real (se crea y borra un archivo temporal)
    bad = SRC / "auth" / "domain" / "_auditoria_tmp.py"
    try:
        bad.write_text("import pymongo\n", encoding="utf-8")
        r = run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_architecture.py"])
        check("OK" if r.returncode != 0 else "FALLA", "T3 el guardián de arquitectura detecta violaciones", "detectó el import prohibido" if r.returncode != 0 else "NO detectó el import prohibido")
    finally:
        bad.unlink(missing_ok=True)
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main() -> int:
    skip_tests = "--no-tests" in sys.argv
    for fn in (check_structure, check_cu_cards, check_context_mapping, check_plan_phases, check_sql_leftovers,
               check_docstrings, check_cline_rules, check_security_static, check_db_docs_in_sync, check_main_wiring):
        try:
            fn()
        except Exception as exc:  # una verificación rota no debe ocultar las demás
            check("FALLA", fn.__name__, f"error al ejecutar: {exc!r}")
    if skip_tests:
        check("OMITIDO", "T* ruff/pytest/guardián", "--no-tests")
    else:
        try:
            check_tests()
        except Exception as exc:
            check("FALLA", "check_tests", f"error al ejecutar: {exc!r}")

    width = max(len(i) for _, i, _ in RESULTS)
    print("AUDITORÍA MECÁNICA DEL KIT\n" + "=" * 26)
    for state, ident, detail in RESULTS:
        print(f"[{state:<8}] {ident:<{width}}  {detail}")
    counts = {s: sum(1 for st, _, _ in RESULTS if st == s) for s in ("OK", "FALLA", "AVISO", "OMITIDO")}
    print("\nRESUMEN: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    return 1 if counts["FALLA"] else 0


if __name__ == "__main__":
    sys.exit(main())
