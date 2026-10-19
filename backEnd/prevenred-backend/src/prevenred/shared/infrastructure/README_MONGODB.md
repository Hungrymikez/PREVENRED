# Persistencia en MongoDB — cómo está configurado PrevenRed

Este documento describe **cómo guarda los datos el backend hoy**, leyendo el código real
(`src/prevenred/**/infrastructure/`), no lo que se planeó. Donde el código y la documentación de diseño
no coinciden, se indica explícitamente en la sección [§12](#12-lo-que-la-documentación-dice-y-el-código-no-hace).

> **Resumen en una frase:** PyMongo síncrono, sin ODM, con **un repositorio por contexto DDD** que traduce
> a mano `documento ↔ entidad`; una clase base común aplica siempre `$set` (nunca reemplaza el documento) y
> los **índices —incluidos los únicos y los TTL— se crean al arrancar** en el `lifespan` de FastAPI.

---

## Índice

1. [Arquitectura de la capa de datos](#1-arquitectura-de-la-capa-de-datos)
2. [Configuración y arranque](#2-configuración-y-arranque)
3. [Cliente, base de datos y dependencia de FastAPI](#3-cliente-base-de-datos-y-dependencia-de-fastapi)
4. [Clase base `BaseMongoRepository`](#4-clase-base-basemongorepository)
5. [Convenciones de mapeo documento ↔ entidad](#5-convenciones-de-mapeo-documento--entidad)
6. [Catálogo de repositorios y colecciones](#6-catálogo-de-repositorios-y-colecciones)
7. [Índices: únicos, parciales, TTL y 2dsphere](#7-índices-únicos-parciales-ttl-y-2dsphere)
8. [Patrones de escritura destacados](#8-patrones-de-escritura-destacados)
9. [Atomicidad y transacciones](#9-atomicidad-y-transacciones)
10. [Pruebas: mongomock vs. MongoDB real](#10-pruebas-mongomock-vs-mongodb-real)
11. [Recetas: agregar una colección o un repositorio](#11-recetas-agregar-una-colección-o-un-repositorio)
12. [Lo que la documentación dice y el código no hace](#12-lo-que-la-documentación-dice-y-el-código-no-hace)
13. [Operación: inspección y mantenimiento](#13-operación-inspección-y-mantenimiento)

---

## 1. Arquitectura de la capa de datos

Cada contexto (`identity`, `incidents`, `fieldwork`, `aid`, …) es un módulo con las mismas cuatro capas:

```
src/prevenred/<contexto>/
├── domain/
│   ├── repositories.py     # PUERTOS: interfaces abstractas (UserRepository, IncidentRepository...)
│   └── *.py                # entidades y reglas de negocio (dataclasses, ids como str)
├── application/            # casos de uso: dependen SOLO de los puertos
└── infrastructure/
    ├── mongo_<algo>_repository.py   # ADAPTADOR: implementa el puerto con PyMongo
    └── indexes.py                   # ensure_indexes(db) del contexto
```

Lo que es de todos vive en `shared/`: `shared/application/` (puertos sin contexto dueño, como
`EventBus` y `CaseCodeGenerator`) y `shared/infrastructure/` (cliente de Mongo, `BaseMongoRepository`, el
adaptador de consecutivos y sus índices).

Reglas que sostienen el diseño:

| Regla | Dónde se ve |
|---|---|
| **El dominio no conoce Mongo** | `domain/` no importa `pymongo` ni `bson`; los ids son `str` de 24 hex |
| **Sin ODM** (nada de Beanie/MongoEngine) | El mapeo es manual y explícito en cada `mongo_*_repository.py` |
| **Un `mongo_*.py` es el único que conoce la forma del documento** | Docstring de `identity/infrastructure/mongo_user_repository.py` |
| **Una colección pertenece a un solo contexto** | Si otro contexto la necesita, usa puerto o evento, no consulta directa |
| **Nada de datos de negocio en el código** | Estados/zonas/niveles viven en `catalogs` (pendiente, ver §12) |

### ¿Por qué sin ODM?

El docstring de `shared/infrastructure/mongo.py` lo justifica: es poco código, mantiene el dominio limpio
(DDD) y es fácil de revisar. El costo es que **toda** la traducción se escribe a mano, y por eso existe una
clase base que evita repetirla (§4).

---

## 2. Configuración y arranque

### 2.1 Variables de entorno

Se leen con `pydantic-settings` en `shared/infrastructure/config.py`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "pereira_responde"
    jwt_secret: str = "cambia-esto-en-produccion-usa-32-bytes-o-mas"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
```

| Variable `.env` | Atributo | Valor por defecto | Notas |
|---|---|---|---|
| `MONGO_URI` | `mongo_uri` | `mongodb://localhost:27017` | En la nube: cadena de **MongoDB Atlas** |
| `MONGO_DB_NAME` | `mongo_db_name` | `pereira_responde` | Nombre de la base |
| `JWT_SECRET` | `jwt_secret` | valor de ejemplo | **Cambiar en producción** |
| `JWT_EXPIRE_MINUTES` | `jwt_expire_minutes` | `60` | Duración de sesión (pendiente O-16) |

- `extra="ignore"`: variables del sistema que no son del proyecto no rompen el arranque.
- `get_settings()` está cacheado con `@lru_cache`: el `.env` se lee **una sola vez por proceso**.
- `.env.example` es la plantilla; `.env` **no se sube a git**.

### 2.2 Base de datos local (Podman/Docker)

`compose.yaml` levanta **un solo nodo** de `mongo:7`:

```yaml
services:
  mongo:
    image: docker.io/library/mongo:7        # nombre completo: Podman no asume el registro
    container_name: mongo
    command: ["--wiredTigerCacheSizeGB", "0.25"]   # limita la memoria (equipo liviano)
    ports: ["27017:27017"]
    volumes: ["mongo_data:/data/db"]
```

```bash
podman compose up -d      # (o docker compose up -d) — ver docs/GUIA_PODMAN.md
```

> ⚠️ Al ser un nodo simple **no hay replica set**, así que **las transacciones multi-documento no están
> disponibles en local**. El diseño evita depender de ellas (§9).

### 2.3 Creación de índices al arrancar

Los índices no se crean con scripts manuales: se crean en el `lifespan` de FastAPI, en `main.py`:

```python
# ÚNICA fuente de verdad: las pruebas importan ESTA lista (tests/conftest.py).
INDEX_INITIALIZERS = [
    identity_indexes, marketplace_indexes, services_indexes, wellbeing_indexes,
    fieldwork_indexes, incidents_indexes, geo_indexes, aid_indexes,
    media_indexes, notifications_indexes, shared_indexes,
]

@asynccontextmanager
async def lifespan(_: FastAPI):
    db = get_db()
    for ensure in INDEX_INITIALIZERS:
        ensure(db)   # idempotente: si el índice ya existe no hace nada
    yield
```

Consecuencias prácticas:

- **Idempotente**: `create_index` con el mismo `name` y las mismas opciones no hace nada la segunda vez
  (con **opciones distintas**, Mongo falla: por eso `shared` no redefine el `caseId` de otras colecciones).
- Sólo corre cuando el proceso arranca de verdad (`uvicorn`), **no** en las pruebas con `TestClient` sin `with`.
- Es **por contexto**: cada `indexes.py` sólo toca sus colecciones, y se registra a mano en `main.py`.
- **Una sola lista**: `tests/conftest.py` la importa de `main.py`; `tests/test_indexes_wiring.py` lo verifica.

El mismo `main.py` arma el generador de códigos de caso (§8.7) con
`create_case_code_generator()` y lo deja en `app.state.case_codes`, listo para los casos de uso que creen
casos.

---

## 3. Cliente, base de datos y dependencia de FastAPI

`shared/infrastructure/mongo.py` son 37 líneas y hacen tres cosas:

```python
@lru_cache
def get_client() -> MongoClient:
    return MongoClient(get_settings().mongo_uri, tz_aware=True)

def get_db() -> Database:
    return get_client()[get_settings().mongo_db_name]

def as_utc(value: datetime | None) -> datetime | None:
    ...
```

| Decisión | Por qué |
|---|---|
| **Un único cliente por proceso** (`@lru_cache`) | El cliente de PyMongo ya es *thread-safe* y mantiene un pool de conexiones; crear uno por petición lo agotaría |
| **`tz_aware=True`** | Para que las fechas salgan con zona horaria (UTC) y se puedan comparar con `utcnow()` |
| **Conexión perezosa** | Crear el cliente **no falla** aunque Mongo esté apagado; el error aparece en la primera operación. Útil para `--reload` y para herramientas que sólo importan la app |
| `get_db()` como **dependencia de FastAPI** | En las pruebas se sustituye con `app.dependency_overrides[get_db] = lambda: db` (§10) |

> `as_utc()` de `mongo.py` es una función **suelta**; los repositorios usan `utc_aware()` de
> `shared/infrastructure/repository.py` (§4), que hace lo mismo. Ver §12.

---

## 4. Clase base `BaseMongoRepository`

Está en `shared/infrastructure/repository.py`. Existe porque **cada repositorio repetía la misma
traducción**: convertir `_id` y referencias a `ObjectId` al escribir, volver a `str` al leer, normalizar
fechas a UTC, usar `$set` en vez de reemplazar, y traducir `DuplicateKeyError` a `ConflictError`.

### 4.1 El contrato: una subclase declara 3 cosas

```python
class BaseMongoRepository(ABC, Generic[T]):
    collection: str = ""                     # nombre de la colección

    @abstractmethod
    def to_document(self, entity: T) -> dict: ...   # entidad -> documento COMPLETO (sólo al insertar)

    @abstractmethod
    def to_entity(self, document: dict) -> T: ...   # documento -> entidad (sin emitir eventos)

    @abstractmethod
    def updates(self, entity: T) -> dict: ...       # campos que ESTE contexto puede cambiar ($set)
```

Y hereda gratis el CRUD:

| Método | Comportamiento |
|---|---|
| `get_by_id(id)` | `find_one({"_id": oid})`; devuelve `None` si el id no es válido o no existe |
| `add(entity)` | `insert_one(to_document(...))`; `DuplicateKeyError` → `conflict_message()` |
| `update(entity)` | `update_one({"_id": ...}, {"$set": updates(entity)})` — **nunca** reemplaza el documento |
| `delete(id)` | `delete_one(...)`; `True` si existía (lo usa la retención, RN-06) |
| `exists(id)` | `count_documents({"_id": oid}, limit=1) == 1` (consulta liviana) |
| `conflict_message()` | `staticmethod` que cada repositorio puede sobrescribir con su mensaje de negocio |

### 4.2 Los helpers de traducción

```python
def to_object_id(value: str | None) -> ObjectId | None:
    """str del dominio -> ObjectId. None si el valor no es un id válido."""

def to_reference(value: str | None) -> ObjectId | None:
    """Id de OTRO documento al que se apunta (userId, ownerId, propertyId...)."""

def to_id_str(value: Any) -> str | None: ...      # ObjectId (o str) -> str
def utc_aware(value: datetime | None) -> datetime | None: ...
```

- `to_object_id` devuelve `None` **en vez de lanzar** cuando el id está mal formado: así se responde
  «no existe» sin filtrar detalles técnicos (G3), en lugar de un 500.
- `to_reference` es un alias semántico de `to_object_id`: deja claro al leer el código que el campo
  apunta a *otro* documento.
- `utc_aware` pone `tzinfo=UTC` si falta. **Hace falta de verdad**: mongomock devuelve las fechas
  *naive* (probado, §10.3), y según el driver el servidor real puede hacer lo mismo.

### 4.3 Regla importante: `$set`, nunca `replace_one`

`update()` sólo envía los campos que declara `updates()`. Esto es lo que permite que **varios casos de uso
escriban el mismo documento sin pisarse**: por ejemplo, `identity` nunca toca `phone` ni `verified` en
`users`, y `incidents` nunca toca `location` ni `type`. Si se usara `replace_one`, el último en escribir
borraría los campos de los demás.

Además, si `updates()` devuelve un dict vacío, `update()` **no escribe nada** (un `$set: {}` sería inválido
en Mongo).

---

## 5. Convenciones de mapeo documento ↔ entidad

Válidas para **todos** los repositorios (`docs/09_rectificacion_bd_mongodb.md` §3):

| Tema | Convención |
|---|---|
| Nombres de colección | **`snake_case`**: `password_resets`, `aid_needs`, `map_layers`, `property_inspections`, `transactions`… El nombre vive en **una sola constante** de su repositorio (§6) |
| Nombres de campo | **BD en `camelCase`** (`caseId`, `reportedBy`, `createdAt`); **Python en `snake_case`** (`case_id`, `reported_by`, `created_at`) |
| Identificador | `_id` es `ObjectId` en Mongo; en el dominio es `str` de 24 hex, así el dominio no importa `bson` |
| Referencias | Campos `...Id` se guardan como `ObjectId` mediante `to_reference()`; `None` si no aplica |
| Fechas | Siempre **UTC**, normalizadas con `utc_aware()` al leer |
| Enums / estados | Se guardan como **String en MAYÚSCULAS** (`"ACTIVE"`, `"SUSPENDED"`, `"PENDIENTE"`, `"VERIFICADO"`, `"BLOQUEADO"`, `"EXPIRADO"`) |
| Roles | `roles` es un **arreglo de códigos** `["TECNICO", "VOLUNTARIO"]`, no `ObjectId` (hallazgo H-01). Guarda **todos** los roles, sin repetir y de **mayor a menor privilegio** |
| Geolocalización | `location` es un **GeoJSON Point**: `{"type": "Point", "coordinates": [longitud, latitud]}` |
| Barrio/comuna | En `users` es un campo **raíz** `neighborhood` (texto), **fuera** de `location` (§5.3) |

> ⚠️ Detalle que muerde: en GeoJSON el orden es **[longitud, latitud]**. En `incidents` el mapeo lo hace
> explícito: `"coordinates": [i.longitude, i.latitude]`, y al leer `latitude = point[1]`, `longitude = point[0]`.

### 5.1 Forma real de un documento `users`

Así queda un documento recién creado (verificado ejecutando el repositorio):

```json
{
  "_id":            ObjectId("..."),
  "name":           "Ana",
  "email":          "ana@x.co",
  "phone":          null,
  "passwordHash":   "$argon2id$v=19$...",
  "roles":          ["TECNICO", "VOLUNTARIO"],
  "status":         "ACTIVE",
  "verified":       false,
  "neighborhood":   "Centro",
  "location":       null,
  "consent":        { "privacyNoticeVersion": "v1", "acceptedAt": "<Date>", "preciseLocationGranted": false },
  "security":       { "failedLoginAttempts": 0, "lockedUntil": null,
                      "mfa": { "enabled": false, "secretEnc": null } },
  "deviceTokens":   [],
  "createdAt":      "<Date>",
  "updatedAt":      "<Date>"
}
```

Notas: `phone` y `verified` se inicializan a `None`/`false` y **`identity` nunca los modifica** (los llenan
otros casos de uso). El id **se genera en el dominio**, no en Mongo: `Entity.id` tiene
`default_factory=new_id` (`shared/domain/ids.py`), y el repositorio lo escribe explícitamente con
`ObjectId(u.id)`. Por eso la entidad ya tiene id **antes** de guardarse y se puede emitir
`UserRegistered(user_id=...)` con él.


### 5.2 Multirrol: el arreglo completo se guarda y el efectivo se calcula

Una cuenta puede tener **varios roles** (Técnico *y* Voluntario, por ejemplo). La base guarda la lista
completa; el código que autoriza sigue leyendo **un** rol (`user.role`), que es el de mayor privilegio:

| Pieza | Qué hace |
|---|---|
| `User.roles: tuple[Role, ...]` | El campo de dominio. En `__post_init__` pasa por `normalize_roles()`: quita repetidos y ordena **de mayor a menor privilegio** |
| `User.role` (**propiedad**, no campo) | `highest_privilege_role(self.roles)`. El nombre en singular se conservó a propósito para no tocar login, MFA, CU-08 ni `require_roles` |
| `mongo_user_repository._roles_from_document()` | Lee **todos** los códigos del arreglo (`Role(code)` valida cada uno). Si el documento no tiene `roles`, asume `CIUDADANO` en vez de romper el inicio de sesión |
| `_to_document()` / `_mutable_fields()` | Escriben `[r.value for r in u.roles]`: `add()` **y** `update()` guardan la lista completa (antes `update()` la colapsaba a un elemento) |
| `TokenPayload.roles` + `.role` | El JWT lleva `roles: [...]`; `role` (singular) se sigue emitiendo para clientes viejos. Un token antiguo (sin `roles`) se lee con su `role` |
| `require_roles(*allowed)` | Deja pasar si la cuenta tiene **alguno** de los roles permitidos |

Orden de privilegio (`identity/domain/role.py`, `PRIVILEGE_ORDER`), de mayor a menor:

```
ADMINISTRADOR > INSPECTOR > PROFESIONAL_SALUD > TECNICO > VOLUNTARIO > CIUDADANO
```

> ⚠️ Ese orden **no** es el de declaración del enum (que sigue el catálogo `roles` y pone `VOLUNTARIO`
> antes de `PROFESIONAL_SALUD`). Por eso el privilegio vive en su propia constante: si alguien reordena
> el enum para que coincida con `docs/db/roles.md`, las autorizaciones no cambian.

Consecuencias prácticas:

- `["CIUDADANO", "TECNICO"]` se guarda como `["TECNICO", "CIUDADANO"]` y **sigue igual tras `update()`**.
  `roles[0]` es siempre el efectivo, así que una consulta hecha a mano en `mongosh` también lo ve primero.
- Quien es `ADMINISTRADOR` **y** `CIUDADANO` **exige MFA** (RN-07): manda el rol efectivo.
- `User.change_role(role)` (CU-08) **sustituye** el conjunto por ese único rol; `grant_role` / `revoke_role`
  agregan o quitan uno sin perder los demás (nunca dejan la cuenta sin roles).

> Sigue en pie: un documento guardado con códigos en minúsculas (`"tecnico"`) hace lanzar `Role("tecnico")`
> al leer. Ver §12.2.

### 5.3 `neighborhood` en la raíz y `location` como GeoJSON

`docs/EQUIVALENCIAS_BD.md` §2 (fila «Ubicación») dejó dos campos con responsabilidades separadas:

| Campo | Qué guarda | Tipo |
|---|---|---|
| `neighborhood` | El **barrio/comuna** que la persona declara (RN-05: nunca la dirección exacta) | `String` en la **raíz** |
| `location` | Sólo la **coordenada**, si algún día se concede ubicación precisa | GeoJSON `Point` **o `null`** |

```json
{ "neighborhood": "Centro", "location": null }                                   // alta normal
{ "neighborhood": "Centro", "location": {"type": "Point", "coordinates": [-75.69, 4.81]} }
```

Cómo lo resuelve `mongo_user_repository.py`:

| Pieza | Qué hace |
|---|---|
| `_to_document()` | Escribe `"neighborhood": u.neighborhood` y `"location": None`. `identity` todavía **no** captura coordenadas (eso es CU-01 paso de ubicación precisa), así que la ubicación nace en `null` |
| `_mutable_fields()` | El `$set` apunta a **`neighborhood`**, no a `location.neighborhood`: así un `update()` no vuelve a crear el objeto de barrio dentro del GeoJSON |
| `_neighborhood_from_document()` | **Lee primero** la raíz y, si no está, `location.neighborhood` (documentos viejos). Devuelve `""` como mucho: ningún documento antiguo rompe el login |

> ⚠️ **Documentos viejos**: hay usuarios guardados como `{"location": {"neighborhood": "Centro"}}`. Se siguen
> leyendo bien (no hay migración en el repo), pero en cuanto se actualicen con `repo.update()` quedarán con el
> barrio en la raíz. Una consulta de `mongosh` que filtre por barrio debe mirar **ambos** sitios mientras
> existan documentos sin migrar:
>
> ```js
> db.users.find({ $or: [ { neighborhood: "Centro" }, { "location.neighborhood": "Centro" } ] })
> ```
>
> El índice `ix_users_neighborhood` (§7.1) sólo indexa la raíz; para los documentos viejos el truco anterior
> recorre la colección. Si la colección crece, conviene un script de migración que copie
> `location.neighborhood` → `neighborhood` y deje `location` en `null`.


---

## 6. Catálogo de repositorios y colecciones

Hay **17 adaptadores** en `infrastructure/`. Todos heredan de `BaseMongoRepository` salvo dos excepciones
marcadas, que escriben con PyMongo directo porque no mapean una sola entidad.

La columna **Constante** es la **única** definición del nombre de la colección: su `indexes.py` y las
pruebas la importan en lugar de repetir la cadena (`tests/test_collection_names.py` lo verifica). El nombre
va en **`snake_case`** (`docs/EQUIVALENCIAS_BD.md`), igual que en `docs/db/*.md`.

| Contexto | Archivo | Clase | Puerto (dominio) | Constante | Colección | Entidad |
|---|---|---|---|---|---|---|
| identity | `identity/infrastructure/mongo_user_repository.py` | `MongoUserRepository` | `UserDirectory` | `COLLECTION` | `users` | `User` |
| identity | `identity/infrastructure/mongo_auth_repository.py` | `MongoSessionRepository` | `SessionRepository` | `SESSIONS` | `sessions` | `Session` |
| identity | `identity/infrastructure/mongo_auth_repository.py` | `MongoPasswordResetRepository` | `PasswordResetRepository` | `PASSWORD_RESETS` | `password_resets` | `PasswordReset` |
| identity | `identity/infrastructure/mongo_mfa_challenge_repository.py` | `MongoMfaChallengeRepository` | `MfaChallengeRepository` | `COLLECTION` | `mfa_challenges` | `MfaChallenge` |
| identity | `identity/infrastructure/mongo_role_audit.py` ⚠️ | `MongoRoleAssignmentAudit` | `RoleAssignmentAudit` | — | `audit_logs` | *ninguna* (sólo inserta) |
| incidents | `incidents/infrastructure/mongo_incident_repository.py` | `MongoIncidentRepository` | `IncidentRepository` | `COLLECTION` | `incidents` | `Incident` |
| fieldwork | `fieldwork/infrastructure/mongo_property_repository.py` | `MongoPropertyRepository` | `PropertyRepository` | `COLLECTION` | `properties` | `Property` |
| fieldwork | `fieldwork/infrastructure/mongo_inspection_repository.py` | `MongoInspectionRepository` | `InspectionRepository` | `COLLECTION` | `property_inspections` | `Inspection` |
| services | `services/infrastructure/mongo_technician_repository.py` | `MongoTechnicianRepository` | `TechnicianRepository` | `COLLECTION` | `technicians` | `TechnicianProfile` |
| marketplace | `marketplace/infrastructure/mongo_marketplace_repository.py` | `MongoReservationRepository` | `ReservationRepository` | `RESERVATIONS` | `reservations` | `Reservation` |
| marketplace | `marketplace/infrastructure/mongo_marketplace_repository.py` | `MongoTransactionRepository` | `TransactionRepository` | `TRANSACTIONS` | `transactions` | `ToolTransaction` |
| wellbeing | `wellbeing/infrastructure/mongo_wellbeing_repository.py` | `MongoConsentRepository` | `ConsentRepository` | `CONSENTS` | `wellbeing_consents` | `Consent` |
| wellbeing | `wellbeing/infrastructure/mongo_wellbeing_repository.py` | `MongoSurveyRepository` ⚠️ | `SurveyRepository` | `SURVEYS` | `wellbeing_surveys` | `SurveyResponse` |
| aid | `aid/infrastructure/mongo_aid_repository.py` | `MongoAidNeedRepository` | `AidNeedRepository` | `NEEDS_COLLECTION` | `aid_needs` | `AidNeed` |
| aid | `aid/infrastructure/mongo_aid_repository.py` | `MongoAidInventoryRepository` | `AidInventoryRepository` | `INVENTORY_COLLECTION` | `aid_inventory` | `AidInventoryItem` |
| geo | `geo/infrastructure/mongo_map_layer_repository.py` | `MongoMapLayerRepository` | `MapLayerRepository` | `COLLECTION` | `map_layers` | `MapLayer` |
| notifications | `notifications/infrastructure/mongo_notification_repository.py` | `MongoNotificationRepository` | `NotificationRepository` | `COLLECTION` | `notifications` | `Notification` |
| media | `media/infrastructure/mongo_file_repository.py` | `MongoFileRepository` | `FileRepository` | `COLLECTION` | `files` | `StoredFile` |

⚠️ **Excepciones al patrón:**
- `MongoSurveyRepository` **no** hereda de `BaseMongoRepository` a propósito: una respuesta de bienestar
  no se edita ni se consulta por id, y exponer `update()` invitaría a «corregir» datos anónimos. Sólo
  implementa `add` y `count_between`: **no hay forma de preguntar por una persona** (ni `last_response_at`,
  ni equivalente). El documento guarda `answers`, `zone`, `triggerEventId` y `createdAt`, nada más.
- `MongoRoleAssignmentAudit` tampoco: no mapea una entidad, sólo inserta. Y escribe en `audit_logs`, que
  **pertenece al contexto `audit`**, no a `identity`: dependencia cruzada deliberada y documentada.

### 6.1 Colecciones con código hoy vs. documentadas sin código

`docs/db/_indice.md` lista 34 colecciones (los 31 del doc 09 más `sessions`, `password_resets`,
`wellbeing_consents`, `wellbeing_indicators` y `mfa_challenges`). **18 tienen código hoy**: las 17 con
repositorio propio más `counters` (§7.2), que no es un repositorio sino el generador de consecutivos.
Las demás están diseñadas pero todavía no implementadas — relevantes porque el doc 09 habla de ellas y
alguien podría buscarlas en el código:

| Sin implementar (diseñadas) | Notas |
|---|---|
| `roles`, `catalogs`, `operational_modes` | Catálogos y modo vigente |
| `resources`, `reviews`, `service_requests` | Marketplace, servicios y cotizaciones embebidas |
| `donations`, `donation_matches` | Aid (sólo existen `aid_needs` y `aid_inventory`) |
| `volunteers`, `assignments` | Voluntariado |
| `wellbeing_indicators` | Bienestar |
| `audit_logs` | Sin repositorio propio: `identity` sólo inserta en ella (⚠️ en la tabla §6) |

> Los nombres son **`snake_case`** en el código y en `docs/db/*.md`, igual que en `docs/EQUIVALENCIAS_BD.md`.
> Antes el código usaba camelCase (`aidNeeds`, `mapLayers`, `passwordResets`…); el renombrado está hecho y
> `tests/test_collection_names.py` falla si alguien vuelve a escribir un nombre viejo. Ver §12.4.
>
> Las colecciones que ya tenían código **conservan su diseño**: del `EQUIVALENCIAS_BD` sólo se aplicó el
> cambio de nombre. Las que siguen «Pendiente» en ese documento deben seguir **la forma de Camilo**
> (`donations` + `donation_matches` embebidos, `service_requests` con `cotizaciones[]`, `resources` única con
> `type`, etc.) cuando se programen.

Colecciones que sólo existen en el doc 09 (no en PrevenRED2 ni en el código): `materials`, `tools`, `quotes`,
`incident_status_history` (el historial de `incidents` va embebido en `historial_estados[]`) y `nlp_analysis`
(embebido en `wellbeing_surveys`).

---

## 7. Índices: únicos, parciales, TTL y 2dsphere

Un `indexes.py` por contexto. Todos exponen `ensure_indexes(db: Database) -> None` y `main.py` los llama
al arrancar. **En MongoDB la unicidad la garantiza el índice, no el código**: por eso hay `DuplicateKeyError`
traducido a `ConflictError` en la capa base, y por eso los tests corren `ensure_indexes` aunque usen mongomock.

Cada `indexes.py` **importa la constante** del nombre de colección desde el repositorio que la posee
(§6), así el nombre no está escrito dos veces: si mañana cambia, cambia en un solo sitio.

Nomenclatura usada en todo el proyecto:

| Prefijo | Significado |
|---|---|
| `uq_` | Único (unique) |
| `ix_` | Índice normal de consulta |
| `ttl_` | TTL (`expireAfterSeconds=0` ⇒ Mongo borra el documento cuando su fecha llega) |
| `geo_` | `2dsphere` |

### 7.1 `identity` — `identity/infrastructure/indexes.py`

| Colección | Índice | Tipo | Para qué |
|---|---|---|---|
| `users` | `email` → `uq_users_email` | **único** | No repetir correo; E1 de CU-01 |
| `users` | `status` → `ix_users_status` | normal | Filtrar activos/suspendidos |
| `users` | `roles + status` → `ix_users_role_status` | compuesto | CU-08 E1: contar administradores activos sin escanear todo |
| `users` | `neighborhood` → `ix_users_neighborhood` | normal | Agrupar cuentas por barrio/comuna (campo **raíz**, §5.3) |
| `sessions` | `jti` → `uq_sessions_jti` | **único** | Un `jti` = un token emitido (CU-02 A4) |
| `sessions` | `userId` → `ix_sessions_user` | normal | Sesiones de una persona |
| `sessions` | `expiresAt` → `ttl_sessions_expires` | **TTL** | Borrar sesiones vencidas sin código |
| `password_resets` | `tokenHash` → `uq_password_resets_hash` | **único** | Se busca por hash, nunca por token |
| `password_resets` | `userId` → `ix_password_resets_user` | normal | Enlaces de una persona |
| `password_resets` | `expiresAt` → `ttl_password_resets_expires` | **TTL** | Los enlaces vencen solos |
| `password_resets` | `userId + createdAt` → `ix_password_resets_user_created` | compuesto | Listar/auditar |
| `mfa_challenges` | `userId + purpose + status + verifiedAt` → `ix_mfa_challenges_user_purpose_status` | compuesto | Un índice sirve a las dos consultas de CU-03 |
| `mfa_challenges` | `expiresAt` → `ttl_mfa_challenges_expires` | **TTL** | Desafíos vencidos fuera |
| `audit_logs` | `actorId + createdAt` → `ix_audit_actor_created` | compuesto | Auditoría por actor |
| `audit_logs` | `resource + resourceId + createdAt` → `ix_audit_resource` | compuesto | Auditoría por recurso afectado |

Salida real de `list_indexes()` (verificada ejecutando `ensure_indexes` sobre mongomock):

```
users -> _id_, uq_users_email, ix_users_status, ix_users_role_status, ix_users_neighborhood
sessions -> _id_, uq_sessions_jti, ix_sessions_user, ttl_sessions_expires
password_resets -> _id_, uq_password_resets_hash, ix_password_resets_user,
                   ttl_password_resets_expires, ix_password_resets_user_created
mfa_challenges -> _id_, ix_mfa_challenges_user_purpose_status, ttl_mfa_challenges_expires
audit_logs -> _id_, ix_audit_actor_created, ix_audit_resource
```

> Los nombres de los **índices** (`uq_`, `ix_`, `ttl_`, `geo_`) llevan la colección en snake_case desde antes:
> `uq_password_resets_hash`, `ttl_mfa_challenges_expires`… Es decir, nunca hubo que renombrar índices, sólo
> colecciones. Eso también hace que el arranque sobre una base vieja **cree** las colecciones nuevas vacías y
> no toque las antiguas: ver el aviso de migración en §12.4.

### 7.2 Resto de contextos

**marketplace** (`reservations`, `transactions`)

| Colección | Índice (`nombre`) | Tipo |
|---|---|---|
| `reservations` | `toolId+startDate+endDate` (`ix_reservations_tool_dates`) | normal — choques de fechas, CU-13 |
| | `requesterId+createdAt(-1)` (`ix_reservations_requester`) | normal |
| | `ownerId+status+createdAt(-1)` (`ix_reservations_owner`) | normal |
| | `toolId+requesterId+createdAt` (`uq_reservations_request`) | **único** — protege reintentos del cliente |
| `transactions` | `buyerId+createdAt(-1)`, `sellerId+createdAt(-1)`, `itemId+status` | normal |

> `transactions` se llamaba `toolTransactions`. Las reservas siguen en su propia colección: son el ciclo de la
> solicitud, no el historial de operaciones (`docs/EQUIVALENCIAS_BD.md` fila 11).

**services** (`technicians`): `userId` (`uq_technicians_user`, **único**), `specialties+verificationStatus`,
`verificationStatus+createdAt` (cola de verificación, CU-18), `verificationStatus+rating(-1)` (ranking, CU-19).

**wellbeing** (`wellbeing_consents`, `wellbeing_surveys`)

| Colección | Índice (`nombre`) | Tipo |
|---|---|---|
| `wellbeing_consents` | `userId+purpose` (`uq_consent_active`) | **único parcial** `{granted: true, revokedAt: null}` |
| | `userId+grantedAt(-1)` (`ix_consent_user_granted`) | normal |
| | `userId+lastSurveyWeekKey` (`ix_consent_user_survey_week`) | normal — límite de 1 encuesta por semana (O-08) |
| `wellbeing_surveys` | `zone+createdAt(-1)`, `createdAt(-1)` | normal — panel por zona, nunca por usuario |

> El límite de **una encuesta por semana** ya no se apoya en la encuesta (que es anónima) sino en el
> consentimiento: `wellbeing_consents.lastSurveyWeekKey` guarda la semana ISO (`2026-W41`) y **nunca la
> hora**. Se escribe con `$max`, así que es idempotente y no retrocede. El índice único
> `uq_surveys_pseudonym_week` se eliminó junto con el campo `pseudonym`: un índice único por persona en la
> encuesta volvería a vincularla con alguien.

**fieldwork** (`properties`, `property_inspections`)

| Colección | Índice (`nombre`) | Tipo |
|---|---|---|
| `properties` | `caseId` (`uq_properties_case`) | **único + sparse** |
| | `clientId` (`uq_properties_client`) | **único parcial** `{clientId: {$type: "string"}}` |
| | `location` (`geo_properties_location`) | **2dsphere** |
| | `createdBy+createdAt(-1)`, `status` | normal |
| `property_inspections` | `propertyId+inspectedAt`, `requiresSecondReview+secondReviewBy` | normal |
| | `clientId` (`uq_inspections_client`) | **único parcial** |

**incidents** (`incidents`): `caseId` (`uq_incidents_case`, **único + sparse**), `location`
(`geo_incidents_location`, **2dsphere**), `status+priority(-1)`, `reportedBy+createdAt(-1)`, `duplicateOf`,
`clientId` (`uq_incidents_client`, **único parcial**).

**geo** (`map_layers`): `name` (`uq_map_layers_name`, **único**), `name+version`, `visibleForRoles`.

**aid** (`aid_needs`, `aid_inventory`): `caseId` (`uq_aid_needs_case`, **único + sparse**), `location`
(`geo_aid_needs_location`, **2dsphere**), `requestedBy`, `status+priority(-1)`; y en inventario
`sourceType+sourceId`, `status+availableQuantity+type`.

**notifications** (`notifications`): `userId+createdAt(-1)`, `userId+readAt`, `status+createdAt`.

**media** (`files`, `media/infrastructure/indexes.py`)

| Colección | Índice (`nombre`) | Para qué |
|---|---|---|
| `files` | `ownerId+createdAt(-1)` (`ix_files_owner_created`) | «mis archivos», `list_by_owner` |
| | `linkedTo.id` (`ix_files_linked_to`) | evidencias de un reporte o inspección, `list_by_link` |
| | `retentionUntil` (`ix_files_retention`) | revisión de RN-06, `list_expired` |

> Es índice **normal**, no TTL: el binario vive en S3/MinIO y hay que borrarlo con código. Si Mongo
> borrara el documento solo, quedaría el binario huérfano.

**shared** (`shared/infrastructure/indexes.py`, `service_requests`)

| Colección | Índice (`nombre`) | Tipo |
|---|---|---|
| `service_requests` | `caseId` (`uq_service_requests_case`) | **único parcial** `{caseId: {$type: "string"}}` |
| `counters` | — | Ninguno: se busca siempre por `_id` |

> `service_requests` todavía no tiene código (`docs/EQUIVALENCIAS_BD.md` fila 12, «Pendiente»). Su índice
> del consecutivo se deja aquí para que no pueda nacer sin la garantía de unicidad. `incidents`,
> `properties` y `aid_needs` **no** se repiten en `shared`: cada uno ya define su `uq_*_case` con su nombre
> y sus opciones, y Mongo no admite dos índices distintos sobre el mismo campo con el mismo nombre.

### 7.3 Por qué «parcial», «sparse» y «TTL»

- **Único parcial** (`partialFilterExpression`) resuelve «único, pero sólo si el campo existe o cumple una
  condición». Ejemplo `clientId`: miles de documentos pueden tenerlo ausente, pero **no puede haber dos con
  el mismo `clientId`**. Esa es la idempotencia de la sincronización offline (CU-37) garantizada en la base,
  aunque dos envíos offline lleguen exactamente a la vez.
- **Sparse** en `caseId` permite que `caseId` falte (documentos sin consecutivo) sin romper el índice único.
- **TTL** con `expireAfterSeconds=0` = «borra cuando `expiresAt` llegue». Es el único mecanismo de limpieza
  de `sessions`, `password_resets` y `mfa_challenges`: no hay cron ni tarea programada en la app. Ojo: el TTL de
  Mongo corre de forma aproximada (unos 60 s de granularidad), no al milisegundo.
- **`2dsphere`** habilita `$geoNear` (§8.4) y exige que `location` sea un GeoJSON válido.


---

## 8. Patrones de escritura destacados

Lo que hace que la capa de datos resista concurrencia **sin transacciones**.

### 8.1 Escritura condicional = control de concurrencia optimista

El patrón que más se repite: **poner la condición en el filtro** del `update`, no en un `if` previo. Si el
filtro no coincide, otra petición ya cambió el documento y `modified_count == 0`.

```python
# aid/mongo_aid_repository.py — reserve_stock()
result = self._items.update_one(
    {"_id": oid, "status": "DISPONIBLE", "availableQuantity": {"$gte": amount}},
    {"$inc": {"availableQuantity": -amount}, "$set": {"updatedAt": utcnow()}},
)
if result.modified_count != 1:
    return False          # no existe, no está DISPONIBLE o ya no alcanza
```

Es atómico porque **una escritura de un solo documento lo es en Mongo**. Con `read → restar en Python →
write` dos coordinadores podrían vender el mismo stock.

### 8.2 `$push` para arreglos embebidos

`incidents.append_inspection()` agrega a la lista `inspections` con `$push`, no leyendo y reescribiendo el
arreglo:

```python
self._incidents.update_one(
    {"_id": oid},
    {"$push": {"inspections": inspection}, "$set": {"updatedAt": inspection["createdAt"]}},
)
```

La inspección es un documento **embebido**: pertenece al reporte y no tiene sentido fuera de él, así que no
necesita colección propia (`incidentStatusHistory` sí sería colección aparte, y aún no existe).

### 8.3 Idempotencia de la sincronización offline (CU-37)

Tres piezas:
1. El celular genera un `clientId` propio.
2. Índice **único parcial** en `clientId` (`incidents`, `properties`, `property_inspections`).
3. Consulta previa `get_by_client_id()` para responder «ya lo tenía» sin duplicar.

Si dos envíos offline llegan a la vez, el índice rechaza el segundo: el duplicado **no se crea aunque el
`if` de la aplicación falle ante la carrera**.

### 8.4 Búsquedas por cercanía: `$geoNear`

```python
pipeline = [
    {"$geoNear": {
        "near": {"type": "Point", "coordinates": [longitude, latitude]},
        "distanceField": "_distanceMeters",
        "maxDistance": radius_m,
        "spherical": True,
    }},
    {"$match": {"duplicateOf": None}},
    {"$limit": limit},
]
```

`$geoNear` **debe ser la primera etapa** del pipeline y exige el índice `2dsphere`. Alimenta la detección de
duplicados de reportes (CU-30). ⚠️ **mongomock no lo soporta**: esas pruebas usan el fixture `real_db`.

### 8.5 Condiciones de carrera resueltas con `$set` acotado

`MongoUserRepository.updates()` **no incluye** `phone` ni `verified`: identity no es dueño de esos campos,
así que no los pisa aunque escriba la misma fila. Igual con Estados y fechas: cada repositorio sólo declara
en `updates()` lo que su contexto puede cambiar.

### 8.6 Vencimiento sin cron

`invalidate_previous()` (password resets) y `expire_stale()` (MFA) no borran: **mueven `expiresAt` al pasado**
o marcan `EXPIRADO`, y el índice TTL de Mongo hace la limpieza. Nunca se escribe un `delete` explícito para
datos vencidos.

### 8.7 Consecutivos sin repetir: `find_one_and_update` con `$inc`

El «número de caso» que ve el ciudadano (`INC-2026-0001`, RF-22) sale de `counters`, **no** de contar
documentos: `count_documents() + 1` daría el mismo número a dos peticiones simultáneas.

```python
# shared/infrastructure/mongo_case_code_generator.py — next_code()
document = self._counters.find_one_and_update(
    {"_id": counter_key(kind, year)},                      # "caseId-INC-2026"
    {"$inc": {"seq": 1}, "$setOnInsert": {"kind": kind.value, "year": year}},
    upsert=True,
    return_document=ReturnDocument.AFTER,                  # el valor YA incrementado
)
return format_code(kind, year, int(document["seq"]))       # INC-2026-0001
```

- Es **una sola operación atómica**: Mongo incrementa y devuelve en el servidor. Dos procesos (o dos
  workers de uvicorn) que llamen a la vez reciben números distintos; la prueba está en
  `tests/shared/test_case_code_generator.py`.
- El `_id` del contador es su nombre (`docs/db/counters.md`): `caseId-{INC|INM|AYU|SRV}-{año}`.
  Un contador por tipo y año ⇒ el consecutivo vuelve a `0001` cada enero **sin borrar nada**, y cada tipo
  de caso lleva su propia serie.
- El puerto es `shared/application/case_code_generator.py` (`CaseCodeGenerator` + `CaseKind`), así que
  ningún caso de uso importa PyMongo.

> **TODO (pendiente de cablear):** el puerto, el adaptador y sus pruebas ya existen, pero los casos de uso
> que crean casos **todavía no existen** (`incidents`, `fieldwork` y `aid` sólo tienen dominio e
> infraestructura; ninguno tiene `application/`). Cuando se programen CU-29 (reporte), CU-17/33 (inmueble)
> y CU-31 (necesidad de ayuda), cada uno recibe `CaseCodeGenerator` por su `dependencies.py` y llama
> `next_code(CaseKind.INCIDENTE | INMUEBLE | AYUDA)` **antes** de `add()`. Mientras tanto los documentos se
> guardan sin `caseId` (los índices son `sparse`), y `main.create_case_code_generator()` deja el adaptador
> armado en `app.state.case_codes`.

---

## 9. Atomicidad y transacciones

| Nivel | Disponibilidad |
|---|---|
| Escritura de **un documento** | **Siempre atómica** (aunque el `compose.yaml` tenga un nodo simple) |
| Transacciones **multi-documento** | Sólo con *replica set*: Atlas sí; el `compose.yaml` local **no** |

Por eso el diseño evita depender de transacciones:

| Operación | Riesgo | Cómo se resuelve hoy |
|---|---|---|
| Reserva de stock (matching donaciones, CU-42) | Dos coordinadores asignan la misma donación | ✅ `update_one` condicional + `$inc` (§8.1) |
| Sincronización offline (CU-37) | Duplicados al reintentar | ✅ Índice único parcial en `clientId` + upsert lógico (§8.3) |
| Bloqueo de cuenta (CU-02 E2) | — | ✅ `$set` de `security.failedLoginAttempts` / `lockedUntil` |
| Cambio de modo (CU-04) | Cerrar el anterior y abrir el nuevo | ⏳ Pendiente: sin transacción; mientras no exista, tratar «sin modo vigente» como COTIDIANO |
| Cambio de estado de incidente (CU-39) | Estado e historial desincronizados | ⏳ Pendiente: `update_one({_id, status: estadoAnterior})` + insertar historial |
| Cambio de rol (CU-08) | Queda sin rastro la auditoría | ✅ Se escribe la auditoría **antes** del cambio y si falla se lanza `ConflictError` (E3) |
| Consecutivo de caso (RF-22) | Dos casos con el mismo número | ✅ `find_one_and_update` + `$inc` + `upsert` en **un solo documento** (§8.7); no necesita transacción |

### 9.1 Si algún día se necesita una transacción

Para usarla hay que conectar contra un replica set (`mongodb+srv://…` de Atlas, o un `mongod` local con
`--replSet`), y **mongomock no la soporta**: habría que probarla con `real_db`.

---

## 10. Pruebas: mongomock vs. MongoDB real

Instalación y ejecución:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .\.venv\Scripts\Activate.ps1)
pip install -r requirements-dev.txt

pytest -q                        # pythonpath=src y testpaths=tests vienen de pytest.ini
ruff check src tests
```

### 10.1 `db` — base en memoria (lo normal)

```python
@pytest.fixture
def db():
    database = mongomock.MongoClient()["pereira_responde_test"]
    for ensure_indexes in INDEX_INITIALIZERS:
        ensure_indexes(database)   # los índices únicos también se prueban
    return database
```

Dos detalles importantes:

- **Se crean los índices de verdad**, en el mismo orden que `main.py`. Por eso las pruebas sí detectan
  violaciones de unicidad: **verificado** — insertar dos `users` con el mismo `email` lanza
  `DuplicateKeyError`, que el repositorio traduce a `ConflictError` («Ese correo ya está registrado…»).
- La lista `INDEX_INITIALIZERS` **se importa de `main.py`**: hay una única fuente de verdad. Si agregas un
  contexto, basta registrarlo allí (`tests/test_indexes_wiring.py` falla si las pruebas usaran otra lista).

### 10.2 `client` — API sin lifespan

```python
@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)   # sin 'with': no ejecuta lifespan (no toca la BD real)
```

El `TestClient(app)` sin `with` **no** dispara el `lifespan`, así que las pruebas nunca intentan conectarse al
Mongo real. Todo lo que entra por HTTP usa la base en memoria por `dependency_overrides`.

### 10.3 Lo que mongomock **no** hace bien (y por qué existe `real_db`)

| Limitación | Consecuencia |
|---|---|
| No soporta `$geoNear` / índices `2dsphere` | Las pruebas de cercanía usan `real_db` |
| No soporta transacciones | Ídem |
| **Devuelve fechas sin `tzinfo`** (naive) | ⚠️ Verificado ejecutando el repositorio: `createdAt.tzinfo is None`. Es exactamente el motivo de `utc_aware()`, y también por eso el código nunca compara una fecha leída **sin** normalizar |
| No valida todas las opciones de índice | Un índice puede «crearse» en mongomock y fallar en el servidor real |

```python
@pytest.fixture
def real_db():
    """Sólo si defines MONGO_TEST_URI (p. ej. mongodb://localhost:27017)."""
    uri = os.getenv("MONGO_TEST_URI")
    if not uri:
        pytest.skip("Define MONGO_TEST_URI para correr pruebas contra MongoDB real")
    ...
```

```bash
# Con el contenedor arriba:
$env:MONGO_TEST_URI="mongodb://localhost:27017"; pytest -q
# (bash) MONGO_TEST_URI=mongodb://localhost:27017 pytest -q
```

Crea una base temporal `prevenred_test_<8 hex>` y la borra al terminar (`drop_database`). Sin la variable, esos
tests se **saltan** (por eso la corrida normal termina con `passed` + `skipped`, sin `failed`).

> ⚠️ Cuidado al correr las pruebas **sin** `dependency_overrides` o con `MONGO_TEST_URI` apuntando a la base de
> desarrollo: `mongomock` está aislado, pero `real_db` sí escribe en un servidor de verdad (en una base aparte).

---

## 11. Recetas: agregar una colección o un repositorio

### 11.1 Agregar un repositorio a un contexto existente

1. **Puerto** en `<ctx>/domain/repositories.py`:

   ```python
   class ThingRepository(ABC):
       @abstractmethod
       def add(self, thing: Thing) -> None: ...
       @abstractmethod
       def get_by_id(self, thing_id: str) -> Thing | None: ...
   ```

2. **Adaptador** en `<ctx>/infrastructure/mongo_thing_repository.py`:

   ```python
   COLLECTION = "things"

   def _to_entity(d: dict) -> Thing: ...
   def _to_document(t: Thing) -> dict: ...

   class MongoThingRepository(BaseMongoRepository[Thing], ThingRepository):
       collection = COLLECTION

       def __init__(self, db: Database) -> None:
           super().__init__(db)
           self._things = self._col

       def to_document(self, thing: Thing) -> dict:
           return _to_document(thing)

       def to_entity(self, document: dict) -> Thing:
           return _to_entity(document)

       def updates(self, thing: Thing) -> dict:
           return {"status": thing.status, "updatedAt": utcnow()}
   ```

3. **Índices** en `<ctx>/infrastructure/indexes.py` (con nombre `uq_`/`ix_`/`ttl_`/`geo_`):

   ```python
   db["things"].create_index("code", unique=True, name="uq_things_code")
   ```

4. **Documentación** en `docs/db/things.md` + fila en `docs/db/_indice.md`.
5. **Pruebas** en `tests/<ctx>/test_thing_repository.py` usando el fixture `db`.

### 11.2 Agregar un contexto nuevo (con colecciones)

1. Crear `src/prevenred/<ctx>/infrastructure/indexes.py` con `ensure_indexes(db)`.
2. Registrarlo en **`main.py` → `INDEX_INITIALIZERS`** (las pruebas lo heredan: la importan de allí).
3. Registrar el router en `create_app()` (`app.include_router(...)`).

### 11.3 Reglas de oro al escribir un mapeo

| ✅ Haz | ❌ No hagas |
|---|---|
| Declarar en `updates()` **sólo** lo que tu contexto es dueño | Meter en `updates()` campos de otros contextos (`phone`, `verified`…) |
| `to_reference(...)` para ids de otros documentos | `ObjectId(valor)` a mano sin validar |
| `utc_aware(...)` al leer fechas | Comparar fechas leídas sin normalizar |
| Normalizar los estados en MAYÚSCULAS | Guardar enums en minúsculas o mezclados |
| Devolver `None`/`False` para id inválido | Dejar subir `InvalidId` como error 500 |
| Confiar en el índice para la unicidad | «Consultar si existe primero» como única defensa (hay carreras) |

---

## 12. Lo que la documentación dice y el código no hace

Esta sección existe para que nadie asuma algo que no está implementado. Todo lo de aquí se comprobó
buscando en `src/`.

### 12.1 `counters` y `caseId`: el generador existe, pero todavía nadie lo llama

- ✅ **El mecanismo ya está implementado**: puerto `shared/application/case_code_generator.py`
  (`CaseCodeGenerator`, `CaseKind`) y adaptador `shared/infrastructure/mongo_case_code_generator.py`
  sobre la colección `counters` con `find_one_and_update($inc, upsert)`. Formatos
  `INC-AAAA-0001`, `INM-AAAA-0001`, `AYU-AAAA-0001` y `SRV-AAAA-0001` (§8.7). Hay prueba de que dos
  llamadas nunca repiten número (`tests/shared/test_case_code_generator.py`).
- ⏳ **Falta el cableado**: ningún caso de uso llama a `next_code()`, porque los casos de uso que crean
  reportes, inmuebles y necesidades de ayuda todavía no existen (esos contextos sólo tienen `domain/` e
  `infrastructure/`). Mientras tanto los documentos se guardan **sin `caseId`**, y los índices
  `uq_incidents_case`, `uq_properties_case` y `uq_aid_needs_case` son únicos **y sparse** justamente para
  permitirlo.

### 12.2 Multirrol: resuelto, con dos salvedades

- ✅ **Resuelto:** `User` guarda y lee **todos** los roles (`roles: tuple[Role, ...]`) y expone `role` como
  propiedad con el de mayor privilegio; `add()` y `update()` escriben la lista completa, y `require_roles`
  deja pasar si la cuenta tiene **alguno**. Detalle en §5.2.
- ✅ **Verificado por prueba:** `["CIUDADANO", "TECNICO"]` se guarda como `["TECNICO", "CIUDADANO"]`,
  sobrevive a `update()` y `roles[0]` sigue siendo el efectivo
  (`tests/identity/test_user_multirole.py`).
- ⚠️ **Salvedad 1 — CU-08 asigna un solo rol:** `change_role()` **sustituye** todo el conjunto (es lo que
  pide el caso de uso). Si un Administrador cambia el rol de una cuenta multirrol, los roles que no asigne
  se pierden. Para agregar sin perder, usar `grant_role()`.
- ⚠️ **Salvedad 2 — datos viejos en minúsculas:** los códigos se guardan en **MAYÚSCULAS**
  (`CIUDADANO`, `TECNICO`, `VOLUNTARIO`, `PROFESIONAL_SALUD`, `INSPECTOR`, `ADMINISTRADOR`). Si existieran
  documentos con `"tecnico"`, `Role("tecnico")` lanza al leer. **No hay script de migración** en el repo.

### 12.3 `files` sin índices: resuelto

`media/infrastructure/indexes.py` crea `ix_files_owner_created` (`ownerId + createdAt(-1)`),
`ix_files_linked_to` (`linkedTo.id`) e `ix_files_retention` (`retentionUntil`), y está registrado en
`INDEX_INITIALIZERS` (§7.2). `retentionUntil` es índice **normal, no TTL**: el binario se borra con código
(RN-06), porque vive en S3/MinIO.

### 12.4 Nombres de colección: snake_case en los docs y en el código

Antes los docs decían `snake_case` y el código usaba camelCase. **Ya coinciden** (`docs/EQUIVALENCIAS_BD.md`
sección 1). Sólo cambió el **nombre**, no el diseño: las colecciones que ya tenían código y pruebas lo
conservan.

| Nombre viejo (código) | Nombre hoy | Constante (archivo dueño) |
|---|---|---|
| `passwordResets` | `password_resets` | `PASSWORD_RESETS` (`mongo_auth_repository.py`) |
| `mfaChallenges` | `mfa_challenges` | `COLLECTION` (`mongo_mfa_challenge_repository.py`) |
| `wellbeingConsents` | `wellbeing_consents` | `CONSENTS` (`mongo_wellbeing_repository.py`) |
| `wellbeingSurveys` | `wellbeing_surveys` | `SURVEYS` (`mongo_wellbeing_repository.py`) |
| `aidNeeds` | `aid_needs` | `NEEDS_COLLECTION` (`mongo_aid_repository.py`) |
| `aidInventory` | `aid_inventory` | `INVENTORY_COLLECTION` (`mongo_aid_repository.py`) |
| `mapLayers` | `map_layers` | `COLLECTION` (`mongo_map_layer_repository.py`) |
| `propertyInspections` | `property_inspections` | `COLLECTION` (`mongo_inspection_repository.py`) |
| `toolTransactions` | `transactions` | `TRANSACTIONS` (`mongo_marketplace_repository.py`) |

Cómo queda garantizado:

- El nombre vive en **una sola constante** del repositorio. Antes estaba escrito a mano también en `indexes.py`
  y en las pruebas; hoy esos módulos **importan** la constante.
- `tests/test_collection_names.py` recorre `src/` y **falla** si aparece cualquiera de los nombres viejos entre
  comillas, y comprueba que cada `indexes.py` crea índices en la colección correcta.
- `sessions`, `users`, `incidents`, `properties`, `technicians`, `reservations`, `notifications`, `files` y
  `audit_logs` ya estaban en `snake_case`: no cambiaron.

> ⚠️ **Migración de una base existente**: los repositorios apuntan ahora a las colecciones nuevas. Si hay datos
> en `aidNeeds`, `mapLayers`, etc., el arranque **no los mueve**: crea colecciones vacías con el nombre nuevo y
> los índices. Los datos viejos hay que pasarlos a mano una vez (por ejemplo con `mongosh`):
>
> ```js
> for (const [vieja, nueva] of Object.entries({
>   passwordResets: "password_resets", mfaChallenges: "mfa_challenges",
>   wellbeingConsents: "wellbeing_consents", wellbeingSurveys: "wellbeing_surveys",
>   aidNeeds: "aid_needs", aidInventory: "aid_inventory",
>   mapLayers: "map_layers", propertyInspections: "property_inspections",
>   toolTransactions: "transactions",
> })) {
>   if (db.getCollectionNames().includes(vieja)) {
>     db[vieja].aggregate([{ $out: nueva }]);   // copia
>     db[vieja].drop();                        // borra la vieja cuando ya copió
>   }
> }
> ```

### 12.4.1 `users.location`: `neighborhood` salió a la raíz

Ya está en el código (§5.3): `neighborhood` es campo raíz y `location` es GeoJSON Point o `null`. **Lo que no
hay** es un script de migración: los documentos con `location.neighborhood` se leen bien
(`_neighborhood_from_document`), pero siguen guardando el barrio dentro de `location` hasta que se actualicen.
Un barrido de una vez:

```js
db.users.find({ neighborhood: { $exists: false }, "location.neighborhood": { $exists: true } })
  .forEach(u => db.users.updateOne(
    { _id: u._id },
    { $set: { neighborhood: u.location.neighborhood }, $unset: { "location.neighborhood": "" } },
  ));
```

### 12.5 Dos funciones UTC que hacen lo mismo

`shared/infrastructure/mongo.py` exporta `as_utc()` y `shared/infrastructure/repository.py` exporta
`utc_aware()`. Son equivalentes; **los repositorios usan `utc_aware()`**. Conviene unificarlas algún día
(todavía pendiente).

### 12.6 Índices documentados que no existen

El doc 09 (§4) lista índices que **no existen** porque sus colecciones tampoco: único en `roles.code` y único
parcial `{active: true}` en `operational_modes`. No los busques en ningún `indexes.py`.

### 12.7 `INDEX_INITIALIZERS` duplicado: resuelto

Antes la lista estaba copiada en `main.py` y en `tests/conftest.py`. Hoy **sólo se define en `main.py`** y
`tests/conftest.py` la importa. `tests/test_indexes_wiring.py` falla si alguien vuelve a copiarla
(compara identidad, no contenido) o si un contexto con colecciones no aporta su `ensure_indexes`.

### 12.8 `mfa_challenges` no aparece en `docs/db/_indice.md`

La colección existe (CU-03) y tiene índices, pero no está listada. Revisa `src/` antes de asumir que un
archivo de `docs/db/` falta por error.

### 12.9 El doc 09 habla de «4 roles fijos»

`docs/09_rectificacion_bd_mongodb.md` (H-01) dice «El dominio tiene 4 roles fijos». Hoy `Role` tiene **6**
códigos. La fuente buena es `identity/domain/role.py`.

### 12.10 Encuesta de bienestar: sin `pseudonym`, y el límite semanal en el consentimiento

Antes `wellbeing_surveys` guardaba `pseudonym` (hash con sal) + `weekKey` y un índice único
`uq_surveys_pseudonym_week`, para limitar a una respuesta por semana. Ese hash **seguía siendo un dato
por persona** en la colección anónima. Ahora:

| Antes | Ahora |
|---|---|
| Documento con `pseudonym` + `weekKey` | Documento **sin ningún dato de la persona**: `answers`, `zone`, `triggerEventId`, `createdAt` |
| Índice único `uq_surveys_pseudonym_week` | **Eliminado** |
| `SurveyRepository.last_response_at(pseudonym)` | **Eliminado**: el puerto sólo tiene `add` y `count_between` |
| Límite semanal = mirar la encuesta | `ConsentRepository.record_survey_sent(user_id, purpose, week_key)` → `wellbeing_consents.lastSurveyWeekKey` |
| `already_sent_this_week(fecha)` | `SurveyResponse.was_sent_in(week_key)` y `Consent.record_survey_sent()` |

Por qué en el consentimiento y no en la encuesta: el consentimiento **ya es** por persona (CU-24), así que
es el único sitio legítimo donde vive «esta persona ya respondió». Guarda `2026-W41` —sólo la semana,
**nunca la hora**— y se escribe con `$max`, de modo que es idempotente y una semana anterior no lo
retrocede. La encuesta queda sin punto de unión: ni siquiera tiene un índice por el que preguntar por
alguien.

Cuidado con `$max` y los documentos nuevos: `to_document` **omite** `lastSurveyWeekKey` cuando es `None`.
Un `null` explícito hace fallar la comparación (`TypeError: '>' not supported between 'str' and
'NoneType'`), porque `$max` no ordena texto contra `null`.

> ⚠️ **Bases existentes**: el arranque crea `lastSurveyWeekKey` y el índice nuevo, pero **no** borra el
> índice viejo de `wellbeing_surveys` ni limpia los documentos que ya tienen `pseudonym`/`weekKey`. En una
> base con datos, hazlo una vez:
>
> ```js
> // 1) retirar el índice que vinculaba la encuesta con una persona
> db.wellbeing_surveys.dropIndex("uq_surveys_pseudonym_week");
> // 2) borrar los campos de identidad de los documentos que ya existen
> db.wellbeing_surveys.updateMany({}, { $unset: { pseudonym: "", weekKey: "" } });
> ```
>
> El punto 2 es irreversible: no hay forma de deshacerlo, porque nunca hubo manera de saber a quién
> pertenecía cada documento. Eso es justo lo que se busca.

---

## 13. Operación: inspección y mantenimiento

### 13.1 Comandos útiles con `mongosh`

```bash
podman exec -it mongo mongosh pereira_responde
```

```js
// ¿Qué índices existen realmente?
db.getCollectionNames().forEach(c => print(c, JSON.stringify(db[c].getIndexes().map(i => i.name))))

// ¿Las fechas están en UTC? (deben ser ISODate con Z)
db.users.find({}, { email: 1, createdAt: 1 }).limit(5)

// Usuarios por rol y estado
db.users.aggregate([
  { $unwind: "$roles" },
  { $group: { _id: { r: "$roles", s: "$status" }, n: { $sum: 1 } } },
])

// Sesiones vigentes (las vencidas las borra el TTL)
db.sessions.countDocuments({ revokedAt: null, expiresAt: { $gt: new Date() } })

// Documentos sin caseId (ver §12.1: el generador existe, aún no se cablea)
db.incidents.countDocuments({ caseId: null })

// Estado de los consecutivos (RF-22): qué números van por tipo y año
db.counters.find().sort({ _id: 1 })

// Tamaño por colección
db.getCollectionNames().forEach(c => print(c, db[c].stats().size))
```

### 13.2 Verificar que los índices se crearon al arrancar

Los índices se crean al **arrancar la app** (`uvicorn`), no al ejecutar `pytest`. Si falta un índice único, la
aplicación no detectará duplicados y devolverá 500 en vez de `ConflictError`:

```bash
uvicorn prevenred.main:app --reload --app-dir src
# en otra terminal:
podman exec -it mongo mongosh pereira_responde --eval "db.users.getIndexes().map(i => i.name)"
```

### 13.3 Copias de seguridad y retención

- Local: los datos viven en el volumen `mongo_data` (`podman volume inspect mongo_data`). `podman compose
  down -v` **borra la base**.
- `files` guarda **sólo metadatos** (`url`, `ownerId`, `accessRoles`, `retentionUntil`); el binario vive en
  S3/MinIO cifrado (RNF-05). Una copia de Mongo **no** respalda las imágenes.
- `audit_logs` es *append-only*: el código sólo inserta, nunca actualiza ni borra.
- `wellbeing_surveys` no tiene id de persona (`answers`, `zone`, `triggerEventId`, `createdAt`), así que no se
  puede «borrar las respuestas de un usuario» (RN-03/RN-05, O-07). El consentimiento de
  `wellbeing_consents` sí es por persona y, además del aviso, guarda la semana del último envío
  (`lastSurveyWeekKey`) para el límite semanal: borrar la cuenta borra esa fila, no las respuestas.

### 13.4 Señales de alarma

| Síntoma | Causa probable |
|---|---|
| `ConflictError` «Ese correo ya está registrado» con correos distintos | Falta `uq_users_email`, o hay datos con mayúsculas sin normalizar (`Email` normaliza con `.strip().lower()` antes de guardar) |
| `ValueError: 'tecnico' is not a valid Role` al leer `users` | Documentos viejos con el rol en minúsculas (§12.2) |
| 500 con un id raro | Se saltó `to_object_id()` en una consulta nueva |
| Reportes offline duplicados | Falta `uq_incidents_client` (índice parcial no creado) |
| Fechas «del futuro» o desfase de horas | Se guardó una fecha **local**: usa `utcnow()` (`shared/domain/events.py`) |
| Documentos vencidos que no desaparecen | El índice TTL no se creó, o `expiresAt` es `null` |
| `$geoNear` falla | Falta el índice `2dsphere` o el GeoJSON está mal (recuerda `[lng, lat]`) |

---

## Anexo: archivos clave

| Archivo | Rol |
|---|---|
| `shared/infrastructure/mongo.py` | Cliente único, `get_db()`, `as_utc()` |
| `shared/infrastructure/config.py` | `Settings` (`.env`): `mongo_uri`, `mongo_db_name` |
| `shared/infrastructure/repository.py` | `BaseMongoRepository` + `to_object_id`, `to_reference`, `to_id_str`, `utc_aware` |
| `shared/infrastructure/mongo_case_code_generator.py` | Consecutivos `caseId` sobre `counters` (§8.7) |
| `shared/infrastructure/indexes.py` | `ensure_indexes(db)` de `shared` (`service_requests.caseId`) |
| `shared/application/case_code_generator.py` | Puerto `CaseCodeGenerator` + `CaseKind` |
| `<ctx>/infrastructure/mongo_*_repository.py` | Mapeo documento ↔ entidad por contexto **y la constante con el nombre de la colección** (§6) |
| `<ctx>/infrastructure/indexes.py` | `ensure_indexes(db)` por contexto; importa la constante del repositorio |
| `identity/domain/role.py` | `Role`, `PRIVILEGE_ORDER`, `normalize_roles()`, `highest_privilege_role()` (§5.2) |
| `main.py` | `INDEX_INITIALIZERS` (única lista) + `lifespan` + `create_case_code_generator()` |
| `tests/conftest.py` | Fixtures `db`, `client`, `real_db` |
| `tests/test_collection_names.py` | Nombres de colección en `snake_case` y definidos una sola vez (§12.4) |
| `tests/test_indexes_wiring.py` | Una sola `INDEX_INITIALIZERS` y un `ensure_indexes` por contexto (§12.7) |
| `docs/09_rectificacion_bd_mongodb.md` | Diseño y hallazgos (H-01…H-11) |
| `docs/EQUIVALENCIAS_BD.md` | Colecciones de PrevenRED2 ↔ código, y qué hacer con cada una |
| `docs/db/*.md` | Una ficha por colección |
| `compose.yaml` | Mongo local (nodo simple, sin transacciones) |
