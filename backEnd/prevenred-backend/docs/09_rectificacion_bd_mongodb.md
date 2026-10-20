# Rectificación del diseño MongoDB (doc 09) frente a los casos de uso (doc 05)

Qué se revisó: las 29 colecciones del doc 09 contra los 48 casos de uso, las reglas de negocio
(RN-01 a RN-07), los requisitos no funcionales y las observaciones O-01 a O-16 del doc 05.

**Veredicto:** el diseño es una buena base. Cubre los 14 módulos y la separación de colecciones es
sensata. Pero hay **cosas que los casos de uso necesitan y la BD no tiene** (por ejemplo, guardar la
contraseña o evitar reportes duplicados al sincronizar). Son 18 hallazgos: 4 críticos, 11 importantes
y 3 menores. Todos están aplicados en `docs/db/<coleccion>.md` (campos marcados con `+` agregado o
`~` cambiado) y en el código del contexto `identity`. **Nada se aplica en el equipo hasta que lo
confirmen**; la sección 6 lista las decisiones que necesito que el equipo valide.

---

## 1. Mapa colección → contexto del backend

| Contexto | Colecciones |
|---|---|
| `identity` | users, roles, **sessions**, **password_resets** |
| `operating_mode` | operational_modes |
| `audit` | audit_logs |
| `notifications` | notifications |
| `marketplace` | materials, tools, reservations, transactions, reviews |
| `services` | technicians, service_requests, quotes |
| `wellbeing` | wellbeing_surveys, nlp_analysis, support_requests, **wellbeing_consents**, **wellbeing_indicators** |
| `incidents` | incidents, incident_status_history |
| `fieldwork` | properties, property_inspections |
| `geo` | map_layers, catalogs |
| `aid` | donations, aid_needs, donation_matches, aid_inventory |
| `volunteering` | volunteers, **assignments** (antes volunteer_assignments) |
| `media` | files |
| `shared` | **counters** |
| `reporting` | ninguna propia: agrega con *aggregation pipelines* |

En **negrita**: colecciones nuevas o renombradas. Regla DDD: **cada colección pertenece a un solo
contexto**; si otro contexto necesita sus datos, los pide por un puerto o por eventos, no consulta
la colección directamente.

---

## 2. Hallazgos

### Críticos

| # | Dónde | Problema | Caso de uso / regla | Ajuste |
|---|---|---|---|---|
| H-03 | `users` | No hay dónde guardar contraseña, aceptación del aviso de privacidad, contador de intentos fallidos, bloqueo ni segundo factor. | CU-01 paso 6, CU-02 E2, CU-03, RN-07 | Agregar `passwordHash`, `consent`, `security{failedLoginAttempts, lockedUntil, mfa}`, `deviceTokens` |
| H-06 | `wellbeing_surveys` | `respondentId` liga cada respuesta de bienestar a una cuenta. El NLP debe ser solo agregado y anónimo, y la política de anonimato está en O-07. | RN-03, RN-05, CU-23, O-07, O-08 | No guardar `respondentId`, ni `userId`, ni `pseudonym`: la encuesta no lleva NINGÚN dato de la persona. El límite de un envío por semana va en `wellbeing_consents.lastSurveyWeekKey` (sólo la semana, nunca la hora). Los resultados por zona van en `wellbeing_indicators` y no se publican con pocas respuestas (umbral pendiente, O-16) |
| H-07 | `incidents`, `properties`, `property_inspections` | Sin un id generado en el celular, cada sincronización puede crear el mismo reporte dos veces. Es justo el problema (reportes duplicados) que PrevenRed quiere resolver. | CU-37, RNF-08, O-02 | `clientId` con índice único parcial + `syncedAt`. La sincronización hace *upsert* por `clientId` |
| H-09 | `aid_needs` | CU-31 «Solicitar ayuda» no tiene colección clara y `aid_needs` no guarda quién la pidió ni su caso. Entonces CU-32 «Consultar estado de mis casos» no puede listarla. | CU-31, CU-32, RF-22, RF-27 | Agregar `requestedBy`, `caseId`, `incidentId` |

### Importantes

| # | Dónde | Problema | Ajuste |
|---|---|---|---|
| H-01 | `users.roles`, `map_layers.visibleForRoles` | Son `ObjectId`: cada petición obligaría a consultar `roles`. El dominio tiene 4 roles fijos. | Guardar **códigos** (`ciudadano`, `inspector`...). `roles` queda como catálogo de permisos |
| H-02 | `roles.permissions` | `Array<String>` no expresa que los permisos cambian según el modo (RF-03). | `Array<{key, modes[]}>` |
| H-04 | (falta) | Cerrar sesión debe revocar el token (CU-02 A4) y recuperar acceso necesita un enlace temporal (A2). | Colecciones `sessions` y `password_resets`, con índice TTL |
| H-05 | `incidents`, `properties`, `aid_needs` | `caseId` es un String sin generador. Un consecutivo mal hecho se duplica con usuarios concurrentes. | Colección `counters` con `findOneAndUpdate($inc)` (atómico) + índice único en `caseId` |
| H-08 | `volunteer_assignments` | Solo sirve a voluntarios, pero CU-38 consulta asignaciones de Inspector y Técnico. | Generalizar a `assignments` con `assigneeId` + `assigneeType` + `propertyId` |
| H-10 | `incidents` | Faltan gravedad, necesidades, referencia a duplicado e inmueble. El documento final dice que el reporte lleva ubicación, tipo, gravedad, necesidades y evidencia. | `severity`, `needs`, `duplicateOf`, `propertyId`, `reportedAt` |
| H-11 | `materials`, `tools`, `aid_inventory` | O-09: falta registrar si el dueño autoriza convertir su material en ayuda. Además `sourceMaterialId` solo apunta a materiales, y el diagrama dibuja `donations → aid_inventory`. | `aidAuthorization` en materials y tools; `sourceType` + `sourceId` en `aid_inventory` |
| H-12 | `reviews`, `materials`, `tools` | CU-16 modera contenido y reseñas, pero no hay estado de moderación. Las reseñas aplican a SegundaVida y OficiosYa. | `moderation{status, reason, reviewedBy}` y `context` |
| H-13 | `files` | RN-06 (control de acceso y retención) y RNF-05 (cifrado) no tienen campos. | `accessRoles`, `linkedTo`, `encrypted`, `retentionUntil` |
| H-14 | `notifications` | CU-06 pide reintentos y CU-07 marca lectura. | `type`, `attempts`, `lastError`, `readAt` |
| H-15 | Todo | El doc no define **índices**. Sin `2dsphere` no hay búsqueda geográfica (RF-07, RNF-03) y sin únicos no hay garantía de correos ni casos sin repetir. | Ver sección 4 y la línea «Índices» de cada ficha |

### Menores

| # | Dónde | Ajuste |
|---|---|---|
| H-16 | `technicians` | `documents`, `verifiedBy`, `verifiedAt`; `verificationStatus` arranca en PENDIENTE (CU-01 paso 7) |
| H-17 | `audit_logs`, `operational_modes` | `actorRole`, `mode`, `ip`, `details`; índice único parcial para que solo exista **un** modo vigente (RN-01) |
| H-18 | `property_inspections` | `requiresSecondReview`, `secondReviewBy` para la doble revisión de casos críticos (O-11) |

### Inconsistencias dentro del doc 09

- El diagrama dibuja `DONATIONS → AID_INVENTORY`, pero el campo es `sourceMaterialId` (apunta a materiales). Hay que decidir de dónde nace el inventario (H-11).
- El diagrama muestra `OPERATIONAL_MODE → USERS` y `MATERIALS → TOOLS`, relaciones que no existen en los campos. Son colecciones independientes; conviene corregir el diagrama.
- El doc usa «Pereira Responde» y los demás documentos «PrevenRed»; unificar el nombre.

---

## 3. Convenciones para todo el backend

- **BD en camelCase** (como el doc 09); **Python en snake_case**. El repositorio traduce.
- `_id` es `ObjectId` en la BD; en el dominio es `str` de 24 hex (`shared/domain/ids.py`), así el dominio no importa `bson`.
- Fechas siempre en UTC. Estados en MAYÚSCULAS. Valores configurables (niveles de daño, estados de incidente, zonas) viven en `catalogs`, no en el código.
- Cada repositorio actualiza con `$set` solo los campos de su contexto, nunca reemplaza el documento entero (así no pisa lo que escriben otros casos de uso).
- Ubicación precisa solo para roles autorizados (RN-05): el repositorio aplica *projection* según el rol; el barrio basta para el resto.
- Sin ODM: PyMongo directo + mapeo manual en `infrastructure/mongo_*_repository.py` (ver `identity/`).

---

## 4. Índices (se crean al arrancar, por contexto)

Cada contexto tiene `infrastructure/indexes.py` con `ensure_indexes(db)` y lo registra en
`main.py`. Resumen de lo crítico:

| Para qué | Índice |
|---|---|
| Búsqueda por cercanía (RF-07, CU-12, CU-19, CU-40) | `2dsphere` en `location` de materials, tools, service_requests, incidents, properties, donations, aid_needs, volunteers |
| No repetir | únicos en `users.email`, `incidents.caseId`, `properties.caseId`, `technicians.userId`, `roles.code`, `sessions.jti` |
| Un solo modo vigente | único **parcial** en `operational_modes` con `{active: true}` |
| Offline sin duplicados | único parcial en `clientId` (incidents, properties, property_inspections) |
| 1 encuesta por semana | `wellbeing_consents.lastSurveyWeekKey` (sólo la semana, nunca la hora) |
| Limpieza automática | TTL en `sessions.expiresAt` y `password_resets.expiresAt` |
| Choques de fechas en alquiler (CU-13) | `{toolId, startDate, endDate}` en `reservations` |

---

## 5. Atomicidad y transacciones

En MongoDB, escribir **un** documento es atómico. Las transacciones entre documentos exigen un
*replica set* (MongoDB Atlas lo es; el `compose.yaml` local es un nodo simple y no). El
diseño evita depender de ellas, salvo en tres casos donde conviene usarlas:

| Operación | Riesgo | Solución |
|---|---|---|
| Cambio de modo (CU-04) | Cerrar el modo anterior y abrir el nuevo: si falla a la mitad, no queda modo vigente | Transacción; mientras no exista, tratar «sin modo vigente» como COTIDIANO |
| Matching (CU-42) | Dos coordinadores asignan la misma donación | `update_one({_id, availableQuantity: {$gte: q}}, {$inc: {availableQuantity: -q}})`: si no coincide, hay conflicto. Luego crear el match |
| Cambio de estado de incidente (CU-39) | Estado y historial desincronizados; dos coordinadores a la vez | `update_one({_id, status: estadoAnterior}, ...)` (si no coincide, otro ya lo cambió) + insertar historial; ideal en transacción |
| Sincronización offline (CU-37) | Duplicados al reintentar | *Upsert* por `clientId` (idempotente) |

---

## 6. Decisiones que el equipo debe confirmar

1. ¿Aceptan **roles como códigos** en vez de `ObjectId` (H-01)? Si no, el código cambia en un solo archivo.
2. ¿Aceptan que las respuestas de bienestar **no guarden el usuario** (H-06)? Es lo que exigen RN-03 y O-07; implica no poder «borrar mis respuestas» por usuario.
3. ¿Aceptan las **5 colecciones nuevas** (`counters`, `sessions`, `password_resets`, `wellbeing_consents`, `wellbeing_indicators`) y renombrar `volunteer_assignments` a `assignments`?
4. ¿Dónde correrá Mongo: **Atlas** (replica set, transacciones) o local? Afecta la sección 5.
5. ¿Dónde se guardan los archivos que referencia `files.url` (GridFS, almacenamiento en la nube)? El doc 09 solo dice «referencia segura».
