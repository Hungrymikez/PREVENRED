# PrevenRed · API (backEnd)

Estado real del backend a día de hoy: **6 rutas HTTP**, un solo contexto con
interfaz (`identity`). El resto de contextos tiene dominio, adaptador de Mongo e
índices, pero **todavía no expone endpoints**.

- **Framework:** FastAPI + Pydantic v2 · **BD:** MongoDB (PyMongo) · **Auth:** JWT (HS256)
- **Arquitectura:** hexagonal por contexto (`domain` → `application` → `infrastructure` / `interface`)
- **Prefijo global de rutas:** `/api/v1`
- **Documentación interactiva:** `/docs` (Swagger UI) y `/openapi.json`
- **Título/versión en OpenAPI:** `PrevenRed API` v`0.2.0`

> Todo lo que aparece aquí se comprobó contra `create_app().openapi()` y contra el
> comportamiento real de las rutas, no contra la documentación previa.

---

## 1. Endpoints

### 1.1 Resumen

| Método | Ruta | CU | Auth | Éxito | Errores posibles |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | CU-01 Registrarse | Pública | `201` | `409`, `422` |
| `POST` | `/api/v1/auth/login` | CU-02 Iniciar sesión | Pública | `200` | `401`, `403`, `429`, `422` |
| `POST` | `/api/v1/auth/mfa/request` | CU-03 paso 1 / A1 | **Bearer** (ver §1.5) | `200` | `401`, `403`, `404`, `409`, `429`, `422` |
| `POST` | `/api/v1/auth/mfa/verify` | CU-03 paso 3 | **Bearer** (ver §1.6) | `200` | `401`, `403`, `404`, `409`, `429`, `422` |
| `POST` | `/api/v1/auth/users` | CU-08 A1 | **Bearer + rol Administrador + MFA** | `201` | `401`, `403`, `409`, `422` |
| `GET` | `/api/v1/auth/me` | (sesión actual) | **Bearer** | `200` | `401`, `404` |

Rutas funcionales totales en el código: **6**. `require_roles` (RBAC) ya está en
uso: protege `POST /auth/users`.

> El **login de Administrador ya no devuelve `500`**: responde `200` con
> `mfa_required: true` y un token temporal (`token_type: "challenge"`) que solo
> sirve para validar el código. La sesión se abre en `POST /auth/mfa/verify`.

### 1.2 `POST /api/v1/auth/register` — CU-01

Crea la cuenta y devuelve sus datos públicos.

**Cuerpo**

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `full_name` | string | sí | 3–150 caracteres; se guarda con `.strip()` |
| `email` | string | sí | formato `algo@dominio.algo`, ≤254; se normaliza a minúsculas |
| `password` | string | sí | 8–128 caracteres |
| `roles` | array | sí | 1–3 elementos; solo `CIUDADANO`, `TECNICO`, `VOLUNTARIO` (mayúsculas) |
| `neighborhood` | string | sí | 1–100 caracteres (barrio/comuna) |
| `privacy_notice_version` | string | **no** | por defecto `"v1"`, ≤20 |
| `accepted_terms` | boolean | sí | debe ser `true`; si no, `422` |

```json
{
  "full_name": "Camila Pérez",
  "email": "camila@mail.com",
  "password": "clave-segura-1",
  "roles": ["VOLUNTARIO", "TECNICO"],
  "neighborhood": "Cuba",
  "accepted_terms": true
}
```

**Respuesta `201`**

```json
{
  "id": "6712f0c0a1b2c3d4e5f60718",
  "full_name": "Camila Pérez",
  "email": "camila@mail.com",
  "role": "TECNICO",
  "roles": ["TECNICO", "VOLUNTARIO"],
  "neighborhood": "Cuba"
}
```

- `role` es el **rol efectivo** (el de mayor privilegio); `roles` viene **de mayor
  a menor privilegio**, así `roles[0] == role`.
- Orden de privilegio: `ADMINISTRADOR > INSPECTOR > PROFESIONAL_SALUD > TECNICO > VOLUNTARIO > CIUDADANO`.
- Nunca se devuelve la contraseña ni su hash.

**Errores**

| Caso | HTTP | Cuerpo del error |
|---|---|---|
| Rol no auto-registrable: `ADMINISTRADOR` (incluido `"admin"` en minúsculas), `INSPECTOR`, `PROFESIONAL_SALUD` | `422` | `validation_error` · `roles.0: El valor no es una de las opciones permitidas.` (el campo es un `Literal` con los tres permitidos) |
| `roles` vacío / en minúsculas / rol no permitido / tipos malos | `422` | `validation_error` (mensaje único que nombra el campo) |
| Correo ya registrado (CU-01 E1) | `409` | `error.code = "conflict"` · `Ese correo ya está registrado. Puedes recuperar tu acceso.` |
| `accepted_terms` falso | `422` | `error.code = "validation_error"` · `Debes aceptar el aviso de privacidad y los términos de uso para crear tu cuenta.` |
| Barrio vacío o solo espacios | `422` | `validation_error` · `Indica tu barrio o comuna.` |
| Correo mal formado | `422` | `validation_error` · `El correo electrónico no tiene un formato válido.` |
| Contraseña < 8 o > 128, nombre < 3 o > 150 | `422` | **Pydantic**: `{"detail": [...]}` con mensajes en inglés (`String should have at least 8 characters`) |

> ⚠️ **Tres observaciones comprobadas:**
> 1. **El rol no auto-registrable responde `422`, no `403`.** El dominio lanza
>    `ForbiddenError` (`Ese tipo de cuenta no se puede crear por auto-registro.`),
>    pero el `Literal` del schema lo rechaza antes
>    (`Input should be 'CIUDADANO', 'TECNICO' or 'VOLUNTARIO'`), así que ese
>    mensaje nunca sale por HTTP. Si el cliente necesita distinguirlo, debe añadir
>    el rol al `Literal` y dejar que decida el dominio.
> 2. **Longitudes: las valida Pydantic, no el dominio.** El mensaje del dominio
>    (`La contraseña debe tener al menos 8 caracteres.`) es hoy inalcanzable por
>    HTTP, y lo que recibe el cliente está en inglés.
> 3. **Dos formatos de error.** Los de Pydantic usan `{"detail": [...]}` y los de
>    dominio `{"error": {"code", "message"}}`. Ver §6.

### 1.3 `POST /api/v1/auth/login` — CU-02

**Cuerpo:** `{"email": "...", "password": "..."}` (ambos `string`).

**Respuesta `200`**

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer", "role": "CIUDADANO" }
```

**Errores**

| Caso | HTTP | `error.code` | Notas |
|---|---|---|---|
| Correo inexistente **o** contraseña incorrecta (E1) | `401` | `unauthorized` | Mensaje **idéntico** siempre: `Correo o contraseña incorrectos.` |
| Correo con formato inválido | `401` | `unauthorized` | Mismo mensaje: no se revela si el correo existe |
| Cuenta bloqueada por intentos (E2) | `429` | `too_many_attempts` | `Demasiados intentos. Intenta de nuevo más tarde.` |
| Cuenta desactivada (E3) | `403` | `forbidden` | `Tu cuenta está desactivada. Comunícate con la entidad.` |
| Cuerpo mal formado (falta `email`/`password`) | `422` | `validation_error` | `email: Falta un dato obligatorio. password: Falta un dato obligatorio.` |

**Bloqueo (RNF-14):** 5 fallos consecutivos → 15 minutos. Cada fallo se guarda
**antes** de responder, y el intento fallido de una cuenta inexistente no deja rastro.

**Cuenta `ADMINISTRADOR` (RN-07): no se emite sesión.** Responde `200` con
`mfa_required: true` y un token **temporal** de `token_type: "challenge"`:

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "challenge",
  "role": "ADMINISTRADOR",
  "mfa_required": true
}
```

- El login deja **abierto el desafío** del segundo factor para la operación `login`
  (colección `mfa_challenges`; el código se guarda solo como hash).
- El token `challenge` **no abre ninguna ruta**: `GET /auth/me`, `POST /auth/users`
  y las rutas de otros contextos responden `401`. Solo lo acepta
  `POST /auth/mfa/verify` con `purpose: "login"`.
- Dura `MFA_TOKEN_MINUTES` (10 min) y sirve para un solo código.
- Secuencia del cliente: `login` → `POST /auth/mfa/verify` → guardar el
  `access_token` con `token_type: "bearer"` que devuelve ese paso.

### 1.4 `POST /api/v1/auth/mfa/request` — CU-03 paso 1 / A1

Entrega un código nuevo del segundo factor para **una operación** de la cuenta dueña
del token. La cuenta **nunca** se toma del cuerpo: la saca del token.

**Cuerpo**

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `purpose` | string | no | operación que se protege; por defecto `"login"`. Usado: `"login"` (CU-02 A1) y `"admin_users"` (CU-08) |
| `method` | string | no | `TOTP`, `SMS` o `EMAIL`; sin valor se conserva/usa el método por defecto |

**Cabecera**

| `purpose` | Token que se envía |
|---|---|
| `login` | `Bearer` con el token `challenge` del login |
| otro (p. ej. `admin_users`) | `Bearer` con la **sesión** ya abierta |

**Respuesta `200`**

```json
{
  "challenge_id": "6712f0c0a1b2c3d4e5f60720",
  "method": "TOTP",
  "code": "483920",
  "expires_at": "2026-10-16T14:05:00+00:00"
}
```

> ⚠️ **`code` sale en la respuesta porque todavía no hay canal de envío** (doc 07,
> O-16). Es una decisión provisional de v1: cuando exista el envío real
> (SMS/correo/TOTP), este campo se quita y el código solo viaja por ese canal.

| Caso | HTTP | `error.code` |
|---|---|---|
| Sin token, o token `challenge` con `purpose` distinto de `login` | `401` | `unauthorized` |
| La cuenta no es `ADMINISTRADOR` (RN-07) | `403` | `forbidden` |
| El `sub` del token ya no existe | `404` | `not_found` |
| Ya hay un código **vigente** para esa operación | `409` | `conflict` |
| Menos de 30 s desde el último código (`MIN_RETRY_AFTER`) | `429` | `too_many_attempts` |

### 1.5 `POST /api/v1/auth/mfa/verify` — CU-03 paso 3

Valida el código. Con `purpose: "login"` **abre la sesión**; con otro propósito
deja la operación crítica autorizada durante `VERIFICATION_TTL` (10 min).

**Cuerpo**

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `purpose` | string | no | por defecto `"login"`; debe coincidir con el del `/mfa/request` |
| `code` | string | sí | se valida en el dominio: un texto mal formado **cuenta como intento fallido** (`401`), no como `422` |

**Respuesta `200`**

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer", "role": "ADMINISTRADOR", "mfa_required": false }
```

- `purpose: "login"` → `access_token` es la **sesión real** (`bearer`): guárdalo y
  usa este token desde ahora. El token `challenge` deja de ser necesario.
- Otro propósito → `access_token: null`, `token_type: null` (la sesión que ya
  tenías sigue siendo la misma; solo se autorizó la operación).

| Caso | HTTP | `error.code` |
|---|---|---|
| Sin token / token de la etapa equivocada para ese `purpose` | `401` | `unauthorized` |
| Código incorrecto, **vencido** o mal formado (E1) | `401` | `unauthorized` (`… Te quedan N intento(s).`) |
| La cuenta no es `ADMINISTRADOR` | `403` | `forbidden` |
| No hay verificación en curso (no se pidió código, o ya se usó) | `409` | `conflict` |
| Intentos agotados (E2, `MFA_MAX_ATTEMPTS = 3`) o operación bloqueada | `429` | `too_many_attempts` |

**Reglas del código:** 6 dígitos, vigencia 5 min (`CODE_TTL`), **un solo uso**, y
comparación en tiempo constante contra el HASH guardado (nunca contra el secreto).

### 1.6 `POST /api/v1/auth/users` — CU-08 A1 (crear cuenta administrativa)

Crea una cuenta de `INSPECTOR` o `ADMINISTRADOR` con credenciales iniciales
generadas por el sistema. Exige **las dos cosas**: rol `ADMINISTRADOR` (RBAC) y la
verificación en dos pasos de la operación `admin_users` vigente (RN-07).

**Cuerpo**

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `full_name` | string | sí | 3–150 |
| `email` | string | sí | formato de correo, ≤254; se normaliza a minúsculas |
| `role` | string | sí | **solo** `INSPECTOR` o `ADMINISTRADOR` |
| `neighborhood` | string | sí | 1–100 |
| `privacy_notice_version` | string | no | por defecto `"v1"` |

La **contraseña no se envía**: se genera aleatoriamente y se devuelve una sola vez.

**Respuesta `201`**

```json
{
  "user": {
    "id": "6712f0c0a1b2c3d4e5f60730",
    "full_name": "Iván Inspector",
    "email": "ivan@prevenred.gov.co",
    "role": "INSPECTOR",
    "roles": ["INSPECTOR"],
    "neighborhood": "Cuba"
  },
  "temporary_password": "K7mQ2xRt9pLw3sZa"
}
```

| Caso | HTTP | `error.code` |
|---|---|---|
| Sin token, o con token `challenge` | `401` | `unauthorized` |
| La cuenta no tiene rol `ADMINISTRADOR` (RBAC) | `403` | `forbidden` |
| Administrador **sin** verificación `admin_users` vigente | `403` | `forbidden` |
| Correo ya registrado | `409` | `conflict` |
| `role` distinto de `INSPECTOR`/`ADMINISTRADOR` o campos inválidos | `422` | `validation_error` |

> ⚠️ **En dominio, solo `ADMINISTRADOR` es cuenta administrativa** (RN-07:
> `Role.is_administrative` es `is Role.ADMINISTRADOR`). Un `INSPECTOR` creado aquí
> **puede iniciar sesión** (recibe su token directamente, sin MFA), pero **no puede
> pedir ni validar el segundo factor** (`403`): las rutas MFA son solo para
> Administradores. Si el Inspector debe operar con MFA, primero hay que ampliar
> `is_administrative` en el dominio.


### 1.7 `GET /api/v1/auth/me`

Requiere cabecera `Authorization: Bearer <access_token>`. Devuelve el mismo
`UserResponse` del registro para la cuenta dueña del token.

| Caso | HTTP | `error.code` |
|---|---|---|
| Sin cabecera `Authorization`, esquema distinto de Bearer, token mal firmado o vencido | `401` | `unauthorized` |
| Token `challenge` (el del login de Administrador, aún sin MFA) | `401` | `unauthorized` |
| El `sub` del token ya no existe en `users` | `404` | `not_found` |

**Ejemplo (PowerShell)** — flujo completo de una cuenta administrativa:

```powershell
$body  = @{ email = "admin@prevenred.gov.co"; password = "clave-admin-1" } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/login `
           -ContentType 'application/json' -Body $body        # token_type = challenge
$hdr   = @{ Authorization = "Bearer $($login.access_token)" }
$code  = (Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/mfa/request `
           -Headers $hdr -ContentType 'application/json' -Body '{}').code
$ses   = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/mfa/verify `
           -Headers $hdr -ContentType 'application/json' `
           -Body (@{ purpose = "login"; code = $code } | ConvertTo-Json)
Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/me `
  -Headers @{ Authorization = "Bearer $($ses.access_token)" }
```
```

> En PowerShell, los acentos de la terminal pueden verse raros (`PÚrez`). Es solo
> la codificación de la consola: los bytes que devuelve la API son UTF‑8 correctos.

---

## 2. Formato de errores

Los errores de negocio los traduce `shared/interface/error_handlers.py`:

```json
{ "error": { "code": "conflict", "message": "Ese correo ya está registrado. Puedes recuperar tu acceso." } }
```

**Todos** los errores de la API usan ese formato: los de dominio, los de
validación de Pydantic y los no previstos. Ya no se responde `{"detail": [...]}`.

| Excepción | HTTP | `code` |
|---|---|---|
| `ValidationError` | `422` | `validation_error` |
| `RequestValidationError` (Pydantic: campo faltante, tipo, `Literal`, longitudes) | `422` | `validation_error` |
| `ConflictError` | `409` | `conflict` |
| `NotFoundError` | `404` | `not_found` |
| `UnauthorizedError` | `401` | `unauthorized` |
| `ForbiddenError` | `403` | `forbidden` |
| `TooManyAttemptsError` | `429` | `too_many_attempts` |
| `DomainError` u otra subclase (p. ej. `StorageError`) | `400` | `storage_error` |
| Error no controlado | `500` | `internal_error` |

Los errores de Pydantic se traducen a **un solo mensaje** que dice qué campo falla:

```json
{ "error": { "code": "validation_error", "message": "full_name: El texto es más corto de lo permitido. roles.0: El valor no es una de las opciones permitidas." } }
```

Los mensajes son claros y accionables: nunca exponen trazas, nombres de
colección ni datos personales (G3 del doc 05).

---

## 3. Autenticación y autorización

### 3.1 Token (JWT HS256)

| Claim | Contenido |
|---|---|
| `sub` | `id` del usuario (string del ObjectId) |
| `role` | rol **efectivo** (string); se conserva por compatibilidad |
| `roles` | **todos** los roles, de mayor a menor privilegio |
| `scope` | `session` (sesión) o `mfa` (token temporal del segundo factor) |
| `iat` / `exp` | emisión y vencimiento |

- Duración: `JWT_EXPIRE_MINUTES` (por defecto **60 minutos**) para la sesión;
  **10 minutos** (`MFA_TOKEN_MINUTES`) para el token `mfa`.
- Firma/verificación: `JWT_SECRET` / `JWT_ALGORITHM` (`HS256`).
- Token inválido o vencido → `401` con
  `Tu sesión no es válida o venció. Inicia sesión de nuevo.`
- Tolerancia: se aceptan tokens antiguos que solo traen `role` (se tratan como
  `scope: session`).
- Un token `scope: mfa` **no** es una sesión: `get_current_token` y `require_roles`
  lo rechazan con `401`. Solo lo aceptan las rutas MFA con `purpose=login`.

> El token **no** se guarda ni se puede revocar todavía: la colección `sessions`
> (CU-02 A4) tiene índices creados, pero el login no escribe en ella.

### 3.2 RBAC (multirrol)

`require_roles(*allowed)` (en `identity/interface/dependencies.py`) deja pasar si
la cuenta tiene **alguno** de los roles indicados: `401` sin token, `403` si no
coincide ninguno. Ya está en uso:

```python
@router.post("/users", dependencies=[Depends(require_roles(Role.ADMINISTRADOR))])
```

`POST /auth/users` combina las dos capas: RBAC por rol (aquí) **y** la verificación
en dos pasos de `admin_users` (la comprueba el caso de uso `ManageUsers`). Ninguna
de las dos sustituye a la otra: el token prueba *quién* entró, el desafío prueba
que pasó el segundo factor.

---

## 4. Cómo ejecutarlo

```powershell
# 1) MongoDB local (Podman o Docker)
podman compose up -d          # o: docker compose up -d

# 2) Dependencias (Python 3.12)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3) Variables de entorno: copia .env.example a .env y ajusta JWT_SECRET

# 4) Arrancar (usa el .venv del proyecto; evita el Python global)
.\.venv\Scripts\python.exe -m uvicorn prevenred.main:app --reload --app-dir src
```

- API: <http://localhost:8000/api/v1/auth/...>
- Swagger UI: <http://localhost:8000/docs>
- Al arrancar, `lifespan` crea todos los índices (`INDEX_INITIALIZERS` en
  `src/prevenred/main.py`) de forma idempotente.

**Configuración** (`.env`, con valores por defecto entre paréntesis):

| Variable | Uso |
|---|---|
| `MONGO_URI` | cadena de conexión (`mongodb://localhost:27017`) |
| `MONGO_DB_NAME` | base de datos (`pereira_responde`) |
| `JWT_SECRET` | secreto de firma — **cambiarlo fuera de desarrollo** |
| `JWT_ALGORITHM` | (`HS256`) |
| `JWT_EXPIRE_MINUTES` | (`60`) |

---

## 5. Qué está implementado y qué no

| Contexto | Dominio | Repositorio Mongo | Índices | **HTTP** |
|---|---|---|---|---|
| `identity` | ✅ | ✅ | ✅ | ✅ **6 rutas** |
| `wellbeing` | ✅ (CU-23/CU-24, encuesta anónima) | ✅ | ✅ | ❌ |
| `marketplace` (reservas) | ✅ | ✅ | ✅ | ❌ |
| `services` (perfil de técnico) | ✅ | ✅ | ✅ | ❌ |
| `aid` (inventario/necesidades) | ✅ | ✅ | ✅ | ❌ |
| `fieldwork` (inmuebles, inspecciones) | ✅ | ✅ | ✅ | ❌ |
| `geo` (capas de mapa) | ✅ | ✅ | ✅ | ❌ |
| `media` (archivos) | ✅ | ✅ | ✅ | ❌ |
| `incidents`, `notifications`, `operating_mode`, `reporting`, `volunteering`, `audit` | parcial | ❌ / parcial | parcial | ❌ |

En `identity` existen como casos de uso, **sin ruta HTTP**: el flujo E de CU-03
(`ResetMfaOnServiceUnavailable`), el resto de CU-08 (`change_role`, `suspend`,
`reactivate`) y `security` (auditoría).

---

## 6. Pendientes que afectan a la API

1. **Canal de envío del código MFA.** Hoy `POST /auth/mfa/request` devuelve `code`
   en la respuesta porque no hay envío real (doc 07, O-16). Al conectar SMS/correo/
   TOTP hay que quitar ese campo y entregar el código solo por el canal.
2. **El gateway del segundo factor vive en memoria del proceso**
   (`InMemorySecondFactorGateway`): si la API corre con varios workers, el código
   emitido por uno no lo valida otro. Con TOTP real esto desaparece.
3. **Un `INSPECTOR` no es cuenta administrativa** (dominio): no puede usar MFA. Si
   CU-08 debe crear Inspectores que operen con segundo factor, ampliar
   `Role.is_administrative`.
4. **CU-08 incompleto por HTTP.** Faltan `PATCH` de rol y suspender/reactivar
   (`ManageUsers.change_role/suspend/reactivate` ya existen y probados).
5. **`create_account` no escribe en `audit_logs`** (CU-05): cambio de rol,
   suspensión y reactivación sí lo hacen; crear la cuenta, no.
6. **Revocación de sesión.** Escribir en `sessions` al hacer login y comprobar el
   `jti` en `get_current_token` (CU-02 A4).
7. **Modo operacional (CU-04).** `require_roles` tiene el TODO de validar el modo
   vigente (Cotidiano/Emergencia).


