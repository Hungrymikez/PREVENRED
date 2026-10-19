# PrevenRed · API (backEnd)

Estado real del backend a día de hoy: **3 rutas HTTP**, un solo contexto con
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
| `POST` | `/api/v1/auth/login` | CU-02 Iniciar sesión | Pública | `200` | `401`, `403`, `429`, `422`, `500`* |
| `GET` | `/api/v1/auth/me` | (sesión actual) | **Bearer** | `200` | `401`, `404` |

\* `500` solo en cuentas `ADMINISTRADOR` (fallo conocido, ver §1.3).

Rutas funcionales totales en el código: **3**. (`require_roles` existe como
fábrica de dependencias RBAC reutilizable, pero **ninguna ruta la usa todavía**.)

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
| Rol no auto-registrable: `ADMINISTRADOR` (incluido `"admin"` en minúsculas), `INSPECTOR`, `PROFESIONAL_SALUD` | `422` | Pydantic: `{"detail": [...]}`, porque el campo es un `Literal` con los tres permitidos |
| `roles` vacío / en minúsculas / rol no permitido / tipos malos | `422` | Pydantic: `{"detail": [...]}` |
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
| Cuerpo mal formado (falta `email`/`password`) | `422` | (Pydantic) | `{"detail": [...]}` |
| Cuenta `ADMINISTRADOR` | `500` | — | Fallo conocido, ver el aviso de abajo |

**Bloqueo (RNF-14):** 5 fallos consecutivos → 15 minutos. Cada fallo se guarda
**antes** de responder, y el intento fallido de una cuenta inexistente no deja rastro.

> 🐞 **Fallo conocido — el login de Administrador por HTTP devuelve `500`.**
> El caso de uso detecta que la cuenta es administrativa y devuelve
> `access_token=None` + `mfa_required=True` (correcto: RN-07 exige segundo
> factor), pero `TokenResponse.access_token` es `str` obligatorio, así que la
> validación de la respuesta falla con `ValidationError` y el servidor responde
> **`500 Internal Server Error`** (verificado). Además, `LoginUser` se arma sin
> `request_mfa`, así que hoy **ni siquiera se envía el código**.
> **Consecuencia:** un `ADMINISTRADOR` no puede obtener token por la API hasta
> que se implemente CU-03 (§6).

### 1.4 `GET /api/v1/auth/me`

Requiere cabecera `Authorization: Bearer <access_token>`. Devuelve el mismo
`UserResponse` del registro para la cuenta dueña del token.

| Caso | HTTP | `error.code` |
|---|---|---|
| Sin cabecera `Authorization`, esquema distinto de Bearer, token mal firmado o vencido | `401` | `unauthorized` |
| El `sub` del token ya no existe en `users` | `404` | `not_found` |

**Ejemplo (PowerShell)**

```powershell
$body  = @{ email = "camila@mail.com"; password = "clave-segura-1" } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/login `
           -ContentType 'application/json' -Body $body
Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/me `
  -Headers @{ Authorization = "Bearer $($login.access_token)" }
```

> En PowerShell, los acentos de la terminal pueden verse raros (`PÚrez`). Es solo
> la codificación de la consola: los bytes que devuelve la API son UTF‑8 correctos.

---

## 2. Formato de errores

Los errores de negocio los traduce `shared/interface/error_handlers.py`:

```json
{ "error": { "code": "conflict", "message": "Ese correo ya está registrado. Puedes recuperar tu acceso." } }
```

| Excepción de dominio | HTTP | `code` |
|---|---|---|
| `ValidationError` | `422` | `validation_error` |
| `ConflictError` | `409` | `conflict` |
| `NotFoundError` | `404` | `not_found` |
| `UnauthorizedError` | `401` | `unauthorized` |
| `ForbiddenError` | `403` | `forbidden` |
| `TooManyAttemptsError` | `429` | `too_many_attempts` |
| `DomainError` u otra subclase (p. ej. `StorageError`) | `400` | `storage_error` |
| Error no controlado / `HTTPException` de FastAPI | `500` | por defecto de FastAPI |

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
| `iat` / `exp` | emisión y vencimiento |

- Duración: `JWT_EXPIRE_MINUTES` (por defecto **60 minutos**).
- Firma/verificación: `JWT_SECRET` / `JWT_ALGORITHM` (`HS256`).
- Token inválido o vencido → `401` con
  `Tu sesión no es válida o venció. Inicia sesión de nuevo.`
- Tolerancia: se aceptan tokens antiguos que solo traen `role`.

> El token **no** se guarda ni se puede revocar todavía: la colección `sessions`
> (CU-02 A4) tiene índices creados, pero el login no escribe en ella.

### 3.2 RBAC (multirrol)

`require_roles(*allowed)` (en `identity/interface/dependencies.py`) deja pasar si
la cuenta tiene **alguno** de los roles indicados: `401` sin token, `403` si no
coincide ninguno. **Ninguna ruta lo usa aún**; sirve de molde para los próximos
contextos:

```python
@router.get("/x", dependencies=[Depends(require_roles(Role.ADMINISTRADOR))])
```

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
| `identity` | ✅ | ✅ | ✅ | ✅ **3 rutas** |
| `wellbeing` | ✅ (CU-23/CU-24, encuesta anónima) | ✅ | ✅ | ❌ |
| `marketplace` (reservas) | ✅ | ✅ | ✅ | ❌ |
| `services` (perfil de técnico) | ✅ | ✅ | ✅ | ❌ |
| `aid` (inventario/necesidades) | ✅ | ✅ | ✅ | ❌ |
| `fieldwork` (inmuebles, inspecciones) | ✅ | ✅ | ✅ | ❌ |
| `geo` (capas de mapa) | ✅ | ✅ | ✅ | ❌ |
| `media` (archivos) | ✅ | ✅ | ✅ | ❌ |
| `incidents`, `notifications`, `operating_mode`, `reporting`, `volunteering`, `audit` | parcial | ❌ / parcial | parcial | ❌ |

En `identity` existen como casos de uso, **sin ruta HTTP**: CU-03
(`RequestMfaCode`, `ResetMfaOnServiceUnavailable`), CU-08 (`ManageUsers`) y
`security` (auditoría).

---

## 6. Pendientes que afectan a la API

1. **CU-03 / login de Administrador (`500`).** Añadir `mfa_required` al contrato
   de respuesta, con `access_token` opcional; cablear `RequestMfaCode` y el
   endpoint que valida el código. Es lo que desbloquea CU-08 por HTTP.
2. **Formato único de error.** Traducir también `RequestValidationError` de
   Pydantic a `{"error": {"code", "message"}}` para que el cliente tenga una sola
   forma de leer errores.
3. **Revocación de sesión.** Escribir en `sessions` al hacer login y comprobar el
   `jti` en `get_current_token` (CU-02 A4).
4. **RBAC en uso.** Aplicar `require_roles` en las nuevas rutas (hoy ningún
   endpoint está protegido por rol, solo por sesión).
5. **Modo operacional (CU-04).** `require_roles` tiene el TODO de validar el modo
   vigente (Cotidiano/Emergencia).


