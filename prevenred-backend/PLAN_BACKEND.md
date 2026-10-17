# Plan del backend PrevenRed (Pereira Responde) — FastAPI + DDD + MongoDB, construido con Cline y DeepSeek

**Versión 3 (consolidada y corregida).** Reemplaza a las versiones anteriores del plan.
Fuentes: doc 05 (48 casos de uso, reglas RN y RNF), doc 09 (diseño MongoDB), documento final del
proyecto. Si el doc 07 (arquitectura) define algo distinto en MFA, sesión o despliegue, manda el doc 07.

---

## 0. Resumen en un minuto

- **Qué:** una API REST en FastAPI con dos modos (Cotidiano / Emergencia), 4 roles y 14 contextos DDD
  que cubren los 48 casos de uso.
- **Base de datos:** MongoDB con el diseño del doc 09, **ya contrastado con los casos de uso**
  (18 ajustes; ver `docs/09_rectificacion_bd_mongodb.md`). Los ajustes esperan confirmación del equipo.
- **Cómo se construye:** Cline + DeepSeek con poco presupuesto. El plan parte cada caso de uso en 3
  tareas pequeñas y le da a Cline un **molde ya probado** (`identity`) para copiar.
- **Qué ya está hecho y probado:** esqueleto de los 14 contextos, núcleo compartido, CU-01 y CU-02
  completos sobre MongoDB, fichas por caso de uso y por colección, reglas para Cline y un
  **guardián automático de la arquitectura**.
- **Meta realista con poco dinero:** las **Fases 1 a 5** (≈ 63 tareas de Cline) entregan los
  **22 casos de uso de prioridad Crítica**. Las Fases 6 a 10 se agregan según presupuesto.

---

## 1. Tus requisitos y cómo se cumple cada uno

| Requisito | Cómo se cumple |
|---|---|
| Backend en **FastAPI** | `src/prevenred/main.py` + un router por contexto. Docs automáticas en `/docs` |
| Hecho con **Cline y DeepSeek** | `.clinerules`, `.clineignore`, prompts listos (sección 9) y flujo en 3 tareas por caso de uso |
| **Poco dinero** en DeepSeek | Sección 6: contexto pequeño, molde para copiar, fichas separadas, sin bucles |
| **Método DDD** con carpetas | 4 capas por contexto (`domain`, `application`, `infrastructure`, `interface`) + `shared` |
| **Bien estructurado** | Una carpeta por contexto, una clase por caso de uso, un archivo por responsabilidad |
| **Comentado** para entender | Docstring por archivo y por clase, marcas `# CU-xx paso n`, explican el **porqué** (regla en `.clinerules`) |
| Base de datos **MongoDB** | PyMongo, repositorios por colección, índices por contexto, 34 fichas de colecciones |
| **No dañar nada** | `tests/test_architecture.py`, `ruff`, commit por caso de uso, carpetas protegidas (sección 8) |

---

## 2. Contenido del repositorio

```
prevenred-backend/
├── PLAN_BACKEND.md              # este documento
├── .clinerules  .clineignore    # reglas para Cline (cortas a propósito)
├── scaffold.py                  # crea carpetas DDD sin gastar tokens
├── requirements.txt  requirements-dev.txt  ruff.toml  pytest.ini  .env.example  compose.yaml
├── docs/
│   ├── GUIA_PODMAN.md                   # MongoDB local con Podman (o Atlas)
│   ├── AUDITORIA_KIT.md                 # instrucciones para que Cline audite el kit
│   ├── 09_rectificacion_bd_mongodb.md   # revisión del doc 09 contra los casos de uso
│   ├── cu/CU-01.md … CU-48.md           # una ficha por caso de uso (extraída del doc 05)
│   ├── db/<coleccion>.md  _indice.md    # una ficha por colección (34) con campos, tipos e índices
│   ├── reglas_transversales.md          # G1–G6, RN-01–07, RNF-01–15, observaciones O-xx
│   └── indice_cu.md                     # los 48 CU con actor, módulo y prioridad
├── tools/gen_db_docs.py         # regenera docs/db/ desde una sola fuente
├── tools/audit_kit.py           # auditoría mecánica del kit (cero tokens)
├── src/prevenred/
│   ├── main.py                  # arma la app, registra routers, índices y suscriptores de eventos
│   ├── shared/                  # núcleo: errores, ids, eventos, config, conexión Mongo
│   ├── identity/                # ✅ CU-01 y CU-02 hechos: ES EL MOLDE
│   └── <otros 13 contextos>/    # esqueleto con README (módulo, CU, colecciones, estado)
└── tests/
    ├── conftest.py              # Mongo en memoria (mongomock) + fixture opcional de Mongo real
    ├── test_architecture.py     # guardián DDD
    └── identity/                # pruebas de dominio, repositorio y API
```

---

## 3. Decisiones técnicas

| Tema | Decisión | Por qué |
|---|---|---|
| Framework | FastAPI + Pydantic v2, funciones síncronas | Más simple (y más barato de generar con un LLM) que async |
| Base de datos | **MongoDB**, diseño del doc 09 | Decisión del equipo; `2dsphere` cubre la búsqueda por cercanía (RF-07, RNF-03) |
| Acceso a datos | **PyMongo directo, sin ODM** | Mapeo manual documento ↔ entidad: dominio limpio y poco código |
| Ids | `str` de 24 hex en el dominio, `ObjectId` solo en infrastructure | El dominio no importa `bson` |
| Índices | `indexes.py` por contexto, se crean al arrancar | En Mongo no hay migraciones de tablas; lo que se versiona son los índices |
| Contraseñas / sesión | Argon2 / JWT de vida corta | CU-02. Duración y renovación pendientes (O-16) |
| MFA (administradores) | TOTP (app autenticadora) | Propuesta para CU-03; el mecanismo final lo define el doc 07 |
| Pruebas | pytest + `mongomock`; Mongo real opcional con `MONGO_TEST_URI` | `2dsphere` y transacciones necesitan Mongo real |
| Calidad | `ruff` + `tests/test_architecture.py` | Gratis; lo corres tú, no la IA |
| Servicios externos (push/SMS, NLP, WhatsApp, almacenamiento) | Siempre detrás de un **puerto** con timeout y reintentos | Regla G4 del doc 05 |

---

## 4. Arquitectura DDD

### 4.1 Capas de cada contexto

```
<contexto>/
├── domain/          REGLAS DE NEGOCIO: entidades, value objects, eventos, puertos de repositorio
├── application/     CASOS DE USO (una clase con execute por CU) y puertos de servicios
├── infrastructure/  DETALLES: repositorios PyMongo, indexes.py, adaptadores (JWT, SMS, NLP...)
└── interface/       HTTP: router, schemas, dependencies (cableado)
```

Dependencias permitidas: `interface → application → domain` e `infrastructure → application/domain`.

### 4.2 Reglas que verifica `tests/test_architecture.py`

1. `domain/` no importa FastAPI, PyMongo, bson, Pydantic, JWT ni Argon2.
2. `application/` no importa FastAPI, PyMongo ni Pydantic.
3. **Un contexto no importa el interior de otro.** Su cara pública es solo `domain/events.py` (eventos)
   y `application/ports.py` (puertos). El cableado (`interface/dependencies.py`, `main.py`) es la excepción.
4. Cada colección pertenece a **un solo** contexto.

### 4.3 Cómo se hablan los contextos

| Necesidad | Mecanismo | Ejemplo |
|---|---|---|
| Avisar que algo pasó | Evento de dominio | `identity` publica `UserRegistered` → `services` crea el perfil «Pendiente» (CU-01 paso 7) |
| Pedir un dato o servicio | Puerto definido por el que lo **consume**, implementado por el dueño y cableado en `dependencies.py` | `incidents` define `FileAttachments`; `media` lo implementa (CU-47) |
| Auditar | Evento → `audit` lo guarda | cambio de modo (CU-04) → CU-05 |

Los suscriptores de eventos se registran en `EVENT_SUBSCRIBERS` de `main.py`.

### 4.4 Mapa de contextos, casos de uso y colecciones

| Contexto | Módulo | Casos de uso | Colecciones MongoDB |
|---|---|---|---|
| `identity` | M01 | CU-01 ✅ CU-02 ✅ CU-03 CU-08 | users, roles, sessions*, password_resets* |
| `operating_mode` | M02 | CU-04 | operational_modes |
| `audit` | M04 | CU-05 CU-09 | audit_logs |
| `notifications` | M03 | CU-06 CU-07 | notifications |
| `geo` | M11 | CU-10 CU-40 CU-48 | map_layers, catalogs |
| `media` | transversal | CU-47 | files |
| `incidents` | M09 | CU-29 CU-30 CU-32 CU-39 | incidents, incident_status_history |
| `fieldwork` | M05 + M10 | CU-34 CU-35 CU-36 CU-37 CU-38 | properties, property_inspections |
| `aid` | M12 (+ CU-31 de M09) | CU-31 CU-33 CU-41 CU-42 | donations, aid_needs, donation_matches, aid_inventory |
| `volunteering` | M13 | CU-43 CU-44 | volunteers, assignments* |
| `marketplace` | M06 | CU-11 a CU-16 | materials, tools, reservations, transactions, reviews |
| `services` | M07 | CU-17 a CU-22 | technicians, service_requests, quotes |
| `wellbeing` | M08 | CU-23 a CU-28 | wellbeing_surveys, nlp_analysis, support_requests, wellbeing_consents*, wellbeing_indicators* |
| `reporting` | M14 | CU-45 CU-46 | ninguna propia (agrega con *aggregation pipelines*) |
| `shared` | — | — | counters* |

`*` = colección nueva o renombrada respecto al doc 09. Nota: **CU-31 «Solicitar ayuda» vive en `aid`**
porque crea `aid_needs`; **CU-32 «Consultar mis casos»** vive en `incidents` y obtiene las solicitudes
de ayuda por un puerto que `aid` implementa.

---

## 5. MongoDB: qué se corrigió del doc 09

Detalle completo, tabla de hallazgos e índices en `docs/09_rectificacion_bd_mongodb.md`. Resumen:

**Cuatro ajustes críticos**

| # | Problema | Ajuste |
|---|---|---|
| H-03 | `users` no puede guardar contraseña, aceptación de privacidad, intentos fallidos ni MFA | `passwordHash`, `consent`, `security`, `deviceTokens` |
| H-06 | `wellbeing_surveys.respondentId` liga respuestas a una cuenta, pero el análisis debe ser anónimo (RN-03, O-07) | Sin `respondentId`; `pseudonym` + `weekKey`; consentimiento aparte |
| H-07 | Sin id de cliente, la sincronización offline duplica reportes (CU-37, RNF-08) | `clientId` único + `syncedAt` en incidents, properties e inspections |
| H-09 | `aid_needs` no guarda quién pidió ni su caso: CU-32 no puede listar «mis casos» | `requestedBy`, `caseId`, `incidentId` |

**Otros ajustes:** roles como códigos (H-01) y permisos por modo (H-02), `sessions` y `password_resets` (H-04),
`counters` para `caseId` (H-05), `assignments` genérica (H-08), campos de incidentes, ayuda, moderación,
archivos y notificaciones (H-10 a H-14), índices (H-15) y tres menores (H-16 a H-18).

**Convenciones:** BD en camelCase y Python en snake_case; fechas UTC; estados en MAYÚSCULAS; valores
configurables en `catalogs`; `$set` solo de los campos del contexto; ubicación precisa solo para roles
autorizados (RN-05).

**Atomicidad:** escribir un documento es atómico. Para cambio de modo (CU-04), matching (CU-42) y estado
de incidente (CU-39) se usan filtros condicionales o transacciones (requieren *replica set*; Atlas lo es).

### Decisiones que el equipo debe confirmar antes de la Fase 1

| # | Pregunta | Si no hay respuesta, el código usa |
|---|---|---|
| 1 | ¿Roles como códigos en vez de `ObjectId`? | Códigos (ya implementado) |
| 2 | ¿Respuestas de bienestar sin guardar el usuario? | Sin usuario (RN-03, O-07) |
| 3 | ¿Aceptan las 5 colecciones nuevas y `assignments`? | Sí |
| 4 | ¿Mongo en Atlas o local? | Local con Podman (`compose.yaml`, ver `docs/GUIA_PODMAN.md`); sin transacciones |
| 5 | ¿Dónde se guardan los archivos de `files.url`? | Puerto `FileStorage` con adaptador en disco para desarrollo |

---

## 6. Cómo hacer rendir el dinero de DeepSeek

Cline reenvía el historial completo en cada llamada, así que el costo crece con el contexto. Todo el
plan busca mantenerlo pequeño.

1. **Piensa aquí, ejecuta allá.** Los diseños difíciles y las decisiones O-xx se resuelven en Claude;
   a DeepSeek le llegan instrucciones cerradas.
2. **Un caso de uso = tareas nuevas** (*New Task*). Un hilo largo se encarece mensaje a mensaje.
3. **Tres prompts por caso de uso**, una capa cada uno. Un prompt grande falla más y se repite.
4. **Copiar el molde.** «Replica `identity/`» sale más barato y consistente que explicar la arquitectura.
5. **Fichas pequeñas.** `docs/cu/CU-xx.md` (~3 KB) y `docs/db/<coleccion>.md` (~1.5 KB) en vez del
   `.docx` de 80 KB o el PDF completo de la BD.
6. **`.clinerules` corto y estable** (~3 KB; se envía en cada llamada). Un inicio de prompt idéntico
   favorece el caché de contexto de DeepSeek; confirma la tarifa vigente en su página de precios.
7. **Modelo estable.** `deepseek-chat`, el que ya te funcionó sin errores de herramientas. Evita
   modelos de razonamiento para escribir código (más tokens de salida).
8. **Lo mecánico, gratis.** `scaffold.py`, `pytest`, `ruff` y el guardián de arquitectura los corres tú.
9. **Errores:** pega solo las últimas ~30 líneas del traceback.
10. **Commit tras cada caso que pase.** Si Cline se enreda, `git restore .` no cuesta nada.
11. **Sin auto-approve** en lecturas de directorios grandes ni comandos largos.
12. **Regla anti-bucle:** si algo falla 2 veces, Cline se detiene (está en `.clinerules`).

**Volumen de trabajo.** 46 casos de uso pendientes × 3 tareas = **≈ 138 tareas pequeñas** en total.
Las Fases 1 a 5 son **63 tareas** y ya incluyen los 22 casos Críticos. Si el dinero se acaba, ahí
tienes un backend completo en lo esencial y el resto queda como ampliación.

---

## 7. Fases

Orden: de lo que otros necesitan a lo que depende de todo. Dentro de cada fase, sigue el orden de la
columna «Casos de uso».

| Fase | Contextos | Casos de uso (en orden) | Entregable | Tareas | Notas |
|---|---|---|---|---|---|
| 0 | — | — | Confirmar las 5 decisiones de la sección 5; arrancar el kit | — | Sin esto, `users` puede cambiar |
| 1 | `identity` | CU-03 MFA, CU-08 Gestionar usuarios y roles | MFA TOTP, alta de Inspector y Administrador, `sessions`, `password_resets`, seed de `roles`, límite de intentos por IP (RNF-14) | 6 | CU-02 A2 y A4 se completan aquí |
| 2 | `audit`, `operating_mode`, `notifications` | CU-05, CU-09, CU-04, CU-06, CU-07 | Auditoría por eventos, cambio de modo con MFA, notificaciones push/SMS tras un puerto | 15 | CU-04 usa CU-03 y CU-05; `users.deviceTokens` |
| 3 | `geo`, `media` | CU-48, CU-47, CU-10 | Ubicación, archivos con control de acceso, catálogos y capas | 9 | Desde aquí, pruebas con Mongo real (`2dsphere`) |
| 4 | `incidents`, `aid` (solo `aid_needs`), `geo` | CU-29, CU-30, CU-31, CU-32, CU-39, CU-40 | Reportes con `caseId` (counters) e idempotencia (`clientId`), solicitud de ayuda, ciclo de vida, mapa multicapa | 18 | Resolver O-10, O-11, O-13 |
| 5 | `fieldwork` | CU-34, CU-35, CU-36, CU-38, CU-37 | Censo, nivel de daño, habitabilidad, asignaciones, sincronización offline | 15 | CU-37 al final: es el más complejo |
| | | | **Hito: los 22 casos Críticos listos** | **63** | |
| 6 | `aid`, `volunteering` | CU-33, CU-41, CU-42, CU-43, CU-44 | Donaciones, banco de ayudas, matching, voluntariado | 15 | Resolver O-09; CU-42 con filtros atómicos |
| 7 | `marketplace` | CU-11 a CU-16 | SegundaVida: publicar, buscar, alquilar, reseñas, moderación | 18 | |
| 8 | `services` | CU-17 a CU-22 | OficiosYa: perfil, verificación, cotización, WhatsApp | 18 | Escucha `UserRegistered` |
| 9 | `wellbeing` | CU-24, CU-23, CU-25, CU-26, CU-27, CU-28 | Consentimiento, encuesta anónima, NLP agregado, apoyo y crisis | 18 | Resolver O-06 y O-07 antes de programar |
| 10 | `reporting` + cierre | CU-45, CU-46 | Dashboard, exportación, observabilidad, despliegue | 6+ | RNF-13 y RNF-12 |

---

## 8. Flujo de trabajo y cómo no dañar nada

**Por cada caso de uso**

1. Cline → **New Task**. Prompt A (dominio). Revisa el resultado.
2. **New Task**. Prompt B (aplicación + infraestructura).
3. **New Task**. Prompt C (interface + prueba de API).
4. En tu terminal: `ruff check src tests` y `pytest -q`. Todo debe quedar en verde, **incluido** `test_architecture.py`.
5. `git commit -m "CU-xx: nombre"` y marca el estado en `src/prevenred/<contexto>/README.md`.
6. Si falla dos veces, usa el prompt D (sección 9).

**Definición de terminado**
- [ ] Flujo principal, alternativos (A) y excepciones (E) de la ficha
- [ ] Reglas RN y criterios de aceptación de la ficha
- [ ] Pruebas de dominio, repositorio y API en verde
- [ ] Comentarios en español con marcas `# CU-xx paso n`
- [ ] Índices del contexto creados en `indexes.py` y registrados en `main.py`
- [ ] Router registrado en `main.py`

**Protecciones**
- `shared/`, `identity/` y `tests/conftest.py` no se tocan salvo que el prompt lo pida (regla en `.clinerules`).
- `tests/test_architecture.py` falla si alguien rompe las capas o mira dentro de otro contexto.
- Nunca se arregla un test cambiándolo para que pase: se arregla el código.
- Una rama por fase (`git switch -c fase-3-geo-media`) y se une a la principal solo con todo en verde.
- Cualquier cambio a `docs/db/` se hace en `tools/gen_db_docs.py` y se regenera.

---

## 9. Prompts listos

**A · Dominio**
```
Contexto: <ctx>. Caso de uso: CU-xx.
Lee solo docs/cu/CU-xx.md y las fichas docs/db/<coleccion>.md de las colecciones del caso.
Copia el estilo de src/prevenred/identity/domain/.
Crea en src/prevenred/<ctx>/domain/: entidad(es), value objects, eventos y el puerto de
repositorio (ABC). Las reglas de la ficha van en la entidad.
Crea tests/<ctx>/test_<algo>_domain.py. Corre pytest -q tests/<ctx>. No toques otras carpetas.
```

**B · Aplicación + infraestructura**
```
Contexto: <ctx>. CU-xx. El dominio ya existe en src/prevenred/<ctx>/domain/.
Replica identity/application/register_user.py para el caso de uso y
identity/infrastructure/ (mongo_user_repository.py e indexes.py) para el repositorio PyMongo.
Usa SOLO las fichas docs/db/<coleccion>.md necesarias. Implementa flujos A y E de docs/cu/CU-xx.md.
Agrega tests del repositorio como tests/identity/test_user_repository.py. No toques interface/.
```

**C · Interface + prueba de API**
```
Contexto: <ctx>. CU-xx. Casos de uso e infraestructura ya existen.
Replica identity/interface/ (schemas, dependencies, router). Protege con require_roles(...)
según el actor de la ficha. Registra el router y ensure_indexes en main.py (una línea cada uno).
Agrega tests/<ctx>/test_<algo>_api.py siguiendo tests/identity/test_auth_api.py.
Corre pytest -q.
```

**D · Arreglar un error** (nueva tarea, con poco contexto)
```
pytest falla en tests/<ctx>/<archivo>. Error (últimas líneas):
<pega ~30 líneas>
Lee solo ese test y el archivo que prueba. Arregla el CÓDIGO, no el test. Explica en 2 líneas.
```

**E · Puerto entre contextos**
```
En <consumidor> agrega el puerto <Nombre> en application/ports.py (ABC, sin importar otros contextos).
En <proveedor> impleméntalo en infrastructure/. Cabléalo en <consumidor>/interface/dependencies.py.
Agrega la prueba. Después corre pytest -q (incluye test_architecture.py).
```

**F · Reaccionar a un evento**
```
En <contexto> crea application/on_<evento>.py que reaccione a <Evento> (definido en
<otro>/domain/events.py) y una función register_handlers(bus). Agrégala a EVENT_SUBSCRIBERS en main.py.
Agrega la prueba.
```

**Contexto nuevo** (primer prompt de cada fase, sin código):
```
Lee src/prevenred/<ctx>/README.md, docs/db/_indice.md (filas del contexto) y las fichas de sus CU.
Propón en 10 líneas el modelo de dominio y los puertos. No escribas código.
```
Apruébalo o ajústalo aquí conmigo antes de generar.

---

## 10. Reglas transversales: dónde se cumple cada una

| Regla (doc 05) | Dónde se implementa |
|---|---|
| G3 Mensajes claros sin datos técnicos (RNF-09) | `shared/interface/error_handlers.py`: formato `{"error": {code, message}}` |
| G4 Falla de servicios externos: timeout, reintentos, degradación (RNF-13) | Adaptadores en `infrastructure/` tras un puerto; `notifications.attempts` |
| G5 y RN-05 Minimización de datos personales | `$set` por contexto; ubicación precisa solo para roles autorizados |
| G6 y RNF-14 Validación en servidor y límite de frecuencia | Schemas Pydantic + límite de intentos (Fase 1) |
| RN-01 y RN-07 Mínimo privilegio y MFA | `require_roles(...)`, CU-03, CU-04 |
| RN-02 Trazabilidad | Eventos de dominio → `audit` (CU-05) |
| RN-03 y RNF-04 NLP solo agregado | `wellbeing`: sin usuario en encuestas, `wellbeing_indicators` con umbral mínimo |
| RN-04 Habitabilidad solo por procedimiento y rol | Reglas en la entidad de `fieldwork`; `require_roles(INSPECTOR)` |
| RN-06 Archivos con acceso y retención | `files.accessRoles`, `retentionUntil` |
| RNF-03 Rendimiento geoespacial | Índices `2dsphere` + `$geoNear` |
| RNF-05 Cifrado | `files.encrypted`, HTTPS en despliegue, secretos en `.env` |
| RNF-08 Offline-first | `clientId` + *upsert* idempotente (CU-37) |
| RNF-13 Observabilidad | Registro estructurado y auditoría (Fase 10) |
| RNF-15 Mantenibilidad | DDD, guardián de arquitectura y `ruff` |

---

## 11. Decisiones pendientes del doc 05 (valores provisionales)

Mientras no se resuelvan, el código usa un valor provisional marcado `TODO(O-xx)`.

| Obs. | Impacto | Provisional |
|---|---|---|
| O-06 / O-07 | Detección de crisis y anonimato (CU-23, CU-28) | CU-28 solo muestra opciones de ayuda; la identidad nunca llega al análisis |
| O-09 | Consentimiento para convertir material en ayuda | `aidAuthorization` del dueño, por defecto `false` |
| O-10 | Quién asigna reportes (CU-39) | El Administrador, manualmente |
| O-11 | Transiciones de incidente | Un estado a la vez; retroceso solo Administrador |
| O-12 | Video en cotización | Solo fotos en v1.0 |
| O-13 | Reporte sin foto | Permitido |
| O-16 | Sesión, MFA, límites de archivo, retención, umbrales | Constantes en `shared/infrastructure/config.py` |

---

## 12. Riesgos y qué hacer

| Riesgo | Mitigación |
|---|---|
| Cline se sale del patrón y genera otro estilo | `.clinerules` + «replica identity» + guardián de arquitectura |
| Se acaba el dinero a mitad | Fases ordenadas por prioridad: 1 a 5 ya cubren lo Crítico |
| Cline entra en bucle arreglando tests | Regla de 2 intentos, prompt D en tarea nueva, `git restore .` |
| `mongomock` oculta un error de índices geográficos | Pruebas con `MONGO_TEST_URI` desde la Fase 3 |
| El equipo cambia el diseño de la BD | Se edita `tools/gen_db_docs.py`, se regenera y se ajusta solo el mapeo del repositorio afectado |
| Datos sensibles de bienestar mal tratados | Decisión 2 de la sección 5 confirmada **antes** de la Fase 9 |

---

## 13. Cómo arrancar

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # cambia JWT_SECRET (y MONGO_URI si usas Atlas)
ruff check src tests && pytest -q                      # 16 passed, 1 skipped (no necesita Mongo)
podman compose up -d                                   # MongoDB local con Podman (ver docs/GUIA_PODMAN.md); omítelo si usas Atlas
uvicorn prevenred.main:app --reload --app-dir src      # http://localhost:8000/docs
MONGO_TEST_URI=mongodb://localhost:27017 pytest -q     # opcional: 17 passed con Mongo real
git init && git add . && git commit -m "Base DDD + MongoDB + identity (CU-01, CU-02)"
```

En Cline abre la carpeta `prevenred-backend` y empieza por la Fase 1 con el prompt A para CU-03.

---

## 14. Qué se corrigió respecto a las versiones anteriores

| Antes | Ahora |
|---|---|
| Plan para SQL (SQLAlchemy, Alembic, PostGIS) | MongoDB con PyMongo, `indexes.py` por contexto, `compose.yaml` (Podman) |
| `UnitOfWork` y ids `UUID` | Eliminado (escritura atómica por documento); ids `str` compatibles con `ObjectId` |
| Diseño del doc 09 usado tal cual | 18 ajustes contra los 48 CU y 34 fichas de colecciones |
| CU-40 (mapa multicapa) no estaba en ninguna fase | Incluido en la Fase 4 |
| CU-31 en `incidents` aunque escribe `aid_needs` | Reubicado en `aid`; CU-32 lo consulta por un puerto |
| Los 22 casos Críticos mezclados con el resto | Fases reordenadas: Fases 1 a 5 = todos los Críticos |
| Los contextos podían importarse entre sí | Cara pública (`events` y `ports`) verificada por prueba automática |
| Sin protección contra daños de la IA | Guardián de arquitectura, `ruff`, carpetas protegidas, prompt D |
| Pruebas solo con base simulada | Fixture opcional de MongoDB real |
