# Auditoría del kit PrevenRed — instrucciones para Cline

> **Cómo se usa:** abre una **tarea nueva** en Cline (*New Task*) y pega:
> `Lee docs/AUDITORIA_KIT.md y ejecútala completa siguiendo sus reglas.`
> Resultado esperado: un único archivo, `docs/auditoria/REPORTE_AUDITORIA.md`, con el veredicto.

## Tu rol
Eres un **auditor independiente**. El kit lo preparó otra IA; no tienes motivo para creerle.
Tu trabajo es decir, con evidencia, si el kit está **bueno para construir el backend de PrevenRed**
(FastAPI + DDD + MongoDB, con Cline y DeepSeek con poco presupuesto) o no.

## Reglas (obligatorias)
1. **Solo lectura.** No edites ni borres nada. El **único** archivo que puedes crear es
   `docs/auditoria/REPORTE_AUDITORIA.md`. No corrijas defectos: repórtalos. Decide el humano.
2. No instales paquetes. Si un comando falla por falta de algo, anótalo como «NO VERIFICADO» y sigue.
3. **Toda afirmación lleva evidencia:** `archivo:línea` o la salida de un comando. Sin evidencia, escribe «NO VERIFICADO». No inventes.
4. Sé escéptico, pero justo: reporta también lo que está bien.
5. **Presupuesto (el dinero es limitado):** máximo ~25 lecturas de archivos y ~6 comandos. No abras
   `docs/cu/` ni `docs/db/` completos: solo las muestras indicadas. No leas `.venv`.
6. Termina cuando el reporte esté escrito. No propongas ni empieces trabajo nuevo.

---

## Paso 1 — Auditoría mecánica (comando, no lectura)
Ejecuta desde la raíz del proyecto, con el entorno virtual activo:
```
python tools/audit_kit.py
```
Pega la salida completa en el reporte. Cada línea `FALLA` es un hallazgo. Cada `AVISO` debes
evaluarlo (¿es riesgo real?). Si el script no corre, ejecuta por separado `ruff check src tests` y `pytest -q`.
Esperado en un kit sano: 0 `FALLA`; `pytest` con `16 passed, 1 skipped`.

## Paso 2 — Lectura dirigida
Lee **solo** estos archivos y responde la pregunta de cada fila.

| Archivo | Qué verificar |
|---|---|
| `.clinerules` | ¿Claro, sin contradicciones y coherente con el código real? ¿Algo que haría que un modelo barato se confunda? |
| `src/prevenred/shared/domain/` (`entity.py`, `ids.py`, `errors.py`) | ¿El id `str` de 24 hex es compatible con `ObjectId`? ¿La igualdad de entidades es correcta? |
| `src/prevenred/identity/domain/user.py` y `role.py` | ¿Cumplen CU-01 y CU-02 (`docs/cu/CU-01.md`, `CU-02.md`): consentimiento obligatorio, sin auto-registro de Inspector/Administrador, bloqueo por intentos? |
| `identity/application/register_user.py`, `login_user.py` | ¿Siguen los pasos y excepciones de las fichas? ¿El orden de validaciones es seguro? |
| `identity/infrastructure/mongo_user_repository.py` | Compáralo con `docs/db/users.md`: campos, tipos y nombres. ¿Qué pasa con `update` si el documento no existe? ¿Qué pasa con `roles` si un usuario tuviera más de un rol? |
| `identity/infrastructure/indexes.py`, `jwt_token_service.py`, `argon2_password_hasher.py` | ¿Índice único real? ¿Expiración del token? ¿Uso correcto de Argon2? |
| `identity/interface/dependencies.py`, `router.py`, `schemas.py` | ¿RBAC correcto? ¿Se valida la entrada? ¿Se expone algún dato sensible? |
| `shared/interface/error_handlers.py` y `src/prevenred/main.py` | ¿Formato de error uniforme? ¿Se registra todo lo necesario? |
| `tests/test_architecture.py`, `tests/conftest.py` | ¿El guardián cubre lo que dice? Busca huecos (por ejemplo, tipos de import que no mira). |
| `PLAN_BACKEND.md` (secciones 4, 6, 7 y 13) | ¿Los nombres de archivos, comandos y cifras coinciden con el código real? |
| `docs/09_rectificacion_bd_mongodb.md` | Toma 4 hallazgos (H-03, H-06, H-07, H-09) y confirma que `docs/db/<colección>.md` los refleja. |
| `docs/GUIA_PODMAN.md`, `compose.yaml`, `.env.example` | ¿Son coherentes entre sí (imagen, puerto, URI)? ¿Un principiante podría seguirlos? |
| **Muestras:** `docs/cu/CU-01.md`, `CU-29.md`, `CU-40.md`; `docs/db/users.md`, `incidents.md`, `aid_needs.md` | ¿Legibles, completas (tablas sin cortar), de tamaño razonable para un modelo? |

## Paso 3 — Hipótesis de defectos (confirma o descarta cada una)
Las anotó el autor del kit. No las asumas ciertas: **pruébalas en el código** y marca
`CONFIRMADA`, `DESCARTADA` o `NO VERIFICADA`, con evidencia.

| # | Hipótesis |
|---|---|
| H1 | Un usuario suspendido con un token todavía vigente sigue autenticado (`get_current_token` y `/me` no revisan `is_active`). |
| H2 | No existe limitación de frecuencia por IP (RNF-14). Confirma si el plan la programa en alguna fase. |
| H3 | El secreto JWT tiene un valor de ejemplo por defecto y nada impide arrancar en producción con él. |
| H4 | El login tarda distinto si el correo no existe que si la contraseña es incorrecta (permitiría deducir qué correos existen). |
| H5 | `MongoUserRepository.update` no falla si el documento no existe. |
| H6 | `update` hace `$set` de `roles` con un solo rol y podría borrar roles adicionales de un documento. |
| H7 | `tests/test_architecture.py` no revisa imports relativos (`from ..otro import x`). |
| H8 | El bus de eventos es síncrono y en memoria: si un suscriptor falla, la petición falla **después** de haber guardado. |
| H9 | `mongomock` puede ocultar diferencias con Mongo real; verifica que exista una prueba opcional con Mongo real. |
| H10 | No hay CORS configurado: un frontend web no podría llamar a la API desde otro origen. |
| H11 | `docs/db/` marca como ajustes (`+`, `~`) cambios que el equipo **aún no aprobó**; verifica que el plan lo advierta para que Cline no los trate como definitivos. |
| H12 | Las cifras del plan («16 passed, 1 skipped», 48 fichas, 34 colecciones, 22 Críticos en las fases 1 a 5) son exactas. |

## Paso 4 — Calificación y veredicto
Puntúa cada criterio de **0** (no cumple), **1** (parcial) o **2** (cumple), con una línea de justificación.

| # | Criterio | Qué mide |
|---|---|---|
| 1 | Funciona | `ruff` y `pytest` en verde; la app arranca; sin errores obvios |
| 2 | Arquitectura DDD | Capas respetadas, dominio puro, protegida por el guardián |
| 3 | Fidelidad a MongoDB | Mapeos, índices y fichas coherentes con el diseño y los ajustes |
| 4 | Cobertura | Los 48 CU asignados a un contexto y programados en el plan |
| 5 | Legibilidad y comentarios | Docstrings útiles que explican el porqué; nombres claros |
| 6 | Seguridad básica | Contraseñas, tokens, errores genéricos, exposición de datos (resultado de H1 a H6 y H10) |
| 7 | Eficiencia con poco presupuesto | `.clinerules` corto, fichas pequeñas, prompts claros, molde replicable |
| 8 | Reproducibilidad | Un principiante puede instalar y arrancar con el plan y la guía de Podman |

**Veredicto por total (máximo 16):**
- **13 a 16 — Bueno:** se puede usar tal cual; corregir lo que reportes en paralelo.
- **9 a 12 — Usable con correcciones:** corregir primero los hallazgos Críticos y Altos.
- **0 a 8 — No usar sin rehacer:** explica qué partes salvar.

Si algún criterio saca **0**, el veredicto no puede ser «Bueno».

Además responde en 5 líneas: **¿conviene que Cline use `identity/` como molde o que se rehaga desde
cero?** Justifica con lo que encontraste (costo de tokens, riesgo de copiar defectos, calidad del molde).

## Paso 5 — Escribe el reporte
Crea `docs/auditoria/REPORTE_AUDITORIA.md` con **esta estructura exacta**:

```markdown
# Reporte de auditoría del kit PrevenRed
Fecha: <hoy> · Auditor: Cline (<modelo>)

## 1. Veredicto
<Bueno / Usable con correcciones / No usar sin rehacer> — <total>/16 — <una frase de razón>

## 2. Puntaje
| # | Criterio | Puntos | Justificación (1 línea) |

## 3. Auditoría mecánica
<salida de python tools/audit_kit.py>

## 4. Hallazgos
| ID | Severidad | Evidencia (archivo:línea) | Qué pasa | Cómo corregirlo | Esfuerzo (S/M/L) |
Severidad: Crítico = rompe o expone datos; Alto = falla en uso normal; Medio = riesgo futuro; Bajo = estilo.

## 5. Hipótesis
| # | Resultado (CONFIRMADA / DESCARTADA / NO VERIFICADA) | Evidencia |

## 6. Muestras de documentación
<2 a 4 líneas: ¿legibles y completas?>

## 7. Lo que está bien
<viñetas cortas>

## 8. ¿Molde `identity/` o rehacer desde cero?
<5 líneas>

## 9. Las 5 correcciones prioritarias
<lista ordenada, cada una con esfuerzo>

## 10. Lo que no pude verificar
<lista honesta>
```
