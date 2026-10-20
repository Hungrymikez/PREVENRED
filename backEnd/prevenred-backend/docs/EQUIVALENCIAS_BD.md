# Equivalencias de base de datos: PrevenRED2 (Camilo) ↔ backend (código real)

**Para guardar como `docs/EQUIVALENCIAS_BD.md`.** Cline lo lee cuando necesite saber cómo se llama algo o qué forma tiene.
La verdad sobre lo ya programado está en `src/prevenred/shared/infrastructure/README_MONGODB.md`.

## Regla de decisión

| Situación de la colección | Qué se hace |
|---|---|
| **Ya tiene código y pruebas** | Se conserva su diseño. Solo se renombra a `snake_case` para coincidir con los nombres de Camilo |
| **Todavía no tiene código** | Se sigue la **forma de PrevenRED2** (colecciones consolidadas y datos embebidos) |
| **No existe en PrevenRED2** | Se crea nueva, en `snake_case`, con los campos opcionales para no romper nada |

Por qué: reescribir lo que ya funciona cuesta créditos y no gana nada. En cambio lo que aún no existe se puede hacer
como el equipo lo diseñó, sin costo extra y con nombres idénticos.

## 1. Las 18 colecciones de PrevenRED2 frente al código

| # | PrevenRED2 | Nombre hoy en el código | Estado | Qué hacer |
|---|---|---|---|---|
| 1 | `roles` | (sin código) | Pendiente | Crear con la forma de Camilo: `name` en MAYÚSCULA, `description`, `permissions`, `active`. Opcional: `emergencyOnly` |
| 2 | `users` | `users` | Implementado, **difiere en campos** | Ver sección 2 |
| 3 | `counters` | (sin código) | Pendiente | Implementar: `_id` = nombre del contador, `sequence_value` |
| 4 | `sessions` | `sessions` | Implementado, igual | Nada |
| 5 | `password_resets` | `passwordResets` | Implementado | **Renombrar** |
| 6 | `wellbeing_consents` | `wellbeingConsents` | Implementado, difiere | **Renombrar.** Se conserva el diseño del código (con `userId`, `granted`, `revokedAt`) porque permite probar y revocar el consentimiento; el de Camilo no. Añade `lastSurveyWeekKey`: la semana del último envío de bienestar, para limitarlo a una por semana |
| 7 | `wellbeing_indicators` | (sin código) | Pendiente | Seguir a Camilo: `zone`, `period`, `metrics`. Agregar `published` (false si hay pocas respuestas) |
| 8 | `operational_modes` | (sin código) | Pendiente | Seguir a Camilo. Índice único parcial `{active: true}` |
| 9 | `audit_logs` | `audit_logs` | Implementado, igual | Nada |
| 10 | `resources` | (sin código; el diseño viejo tenía `materials` y `tools`) | Pendiente | **Seguir a Camilo:** una sola colección con `type` HERRAMIENTA o MATERIAL |
| 11 | `transactions` | `toolTransactions` | Implementado | **Renombrar** a `transactions`. `reservations` se queda aparte (ciclo de la solicitud) |
| 12 | `service_requests` | (sin código) | Pendiente | Seguir a Camilo: cotizaciones **embebidas** en `cotizaciones[]` (cada una con su `_id`). Sin colección `quotes` |
| 13 | `wellbeing_surveys` | `wellbeingSurveys` | Implementado, difiere | **Renombrar.** El `nlp_analysis` va embebido (como Camilo). Ya no guarda `pseudonym` ni `weekKey`: el documento no tiene NINGÚN dato de la persona. El límite de una por semana vive en `wellbeing_consents.lastSurveyWeekKey` (sólo la semana, nunca la hora) |
| 14 | `incidents` | `incidents` | Implementado | Historial **embebido** en `historial_estados[]` (como Camilo), sin colección `incident_status_history`. La inspección va en `property_inspections` |
| 15 | `assignments` | (sin código) | Pendiente | Seguir a Camilo: `assigneeId`, `taskType`, `referenceId`, `status`, `assignedBy` |
| 16 | `aid_management` | `aidNeeds` + `aidInventory` | Implementado, **difiere** | **Renombrar** a `aid_needs` y `aid_inventory`. Las donaciones entran a `aid_inventory` y sus coincidencias van embebidas en `matches` (como `matches_asignados` de Camilo) |
| 17 | `notifications` | `notifications` | Implementado, igual | Nada |
| 18 | `catalogs` | (sin código) | Pendiente | Seguir a Camilo: `name`, `version`, `active`, `items[]` |

## 2. La colección `users`

| Tema | Camilo (PrevenRED2) | Código hoy | Decisión |
|---|---|---|---|
| Hash de contraseña | `password_hash` | `passwordHash` | Se conserva `passwordHash` (el frontend no lo lee). Cambiar solo si el frontend lee Mongo directo |
| Estado | `ACTIVO` / `SUSPENDIDO` | `ACTIVE` / `SUSPENDED` | Igual que arriba |
| Ubicación | GeoJSON Point | `{neighborhood}` | **Corregir:** `neighborhood` pasa a campo raíz; `location` es solo un GeoJSON Point o `null` (RN-05) |
| Perfil técnico | `perfil_tecnico` dentro de `users` | colección `technicians` aparte | Se conserva `technicians` (ya tiene código y pruebas). Mover a `users.perfil_tecnico` es una mejora opcional |
| Perfil voluntario | `perfil_voluntario` dentro de `users` | (sin código) | **Seguir a Camilo** cuando se programe CU-44 |
| Consentimiento, seguridad, tokens | no existen | `consent`, `security`, `deviceTokens` | Se conservan (los exigen CU-01, CU-02, CU-03 y CU-06) |
| Roles | arreglo de MAYÚSCULAS | arreglo de MAYÚSCULAS (6 códigos) | Igual. Falta que el dominio **no pierda** roles al actualizar |

## 3. Colecciones que solo existen en el código (no están en PrevenRED2)

`properties`, `property_inspections`, `map_layers`, `files`, `reservations`, `technicians`, `mfa_challenges`.
Todas en `snake_case`. Las que faltan por programar (`reviews`, `support_requests`) nacen igual.

## 4. Reglas para lo que falta por programar

1. Antes de crear una colección, buscar su fila en la tabla de la sección 1 y seguir la forma indicada.
2. Nombres de colección en `snake_case`. Campos nuevos en `camelCase`. Campos que ya existen en PrevenRED2 conservan su nombre (`costo_diario`, `perfil_tecnico`, `historial_estados`...).
3. Lo nuevo es siempre **opcional** en validadores e índices, para no romper al frontend.
4. Los estados y valores que el doc 05 deja como catálogo (niveles de daño, estados de incidente) se validan contra `catalogs`, no con listas fijas.
5. Estados de incidente (doc 05): `REPORTADO`, `EN_REVISION`, `ASIGNADO`, `EN_ATENCION`, `RESUELTO`.
