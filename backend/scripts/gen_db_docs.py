"""
gen_db_docs.py — Genera docs/db/<coleccion>.md a partir de UNA sola fuente (este archivo).

Fuente: documento 09 (diseño MongoDB) + ajustes propuestos tras contrastarlo con el doc 05.
Marcas en los campos:   (sin marca) = tal cual el doc 09 | + = campo AGREGADO | ~ = campo CAMBIADO.
Uso:  python tools/gen_db_docs.py
Si el equipo acepta o rechaza un ajuste, se edita aquí y se regenera (Cline lee solo la ficha de su colección).
"""
from pathlib import Path

# (nombre, contexto, casos de uso, para qué sirve, campos, índices)
C = []
def col(name, ctx, cus, purpose, fields, indexes=""):
    C.append((name, ctx, cus, purpose, fields.strip(), indexes.strip()))

col("users","identity","CU-01 CU-02 CU-03 CU-08 CU-06","Identidad, contacto, rol, estado y seguridad de la cuenta.","""
_id|ObjectId|Identificador
name|String|Nombre completo
email|String|Correo (único, en minúsculas)
phone|String|Teléfono
~roles|Array<String>|Códigos de rol (antes Array<ObjectId>; ver H-01)
status|String|ACTIVE / SUSPENDED
verified|Boolean|Verificación
location|Object|Ubicación autorizada. Incluye neighborhood (barrio/comuna)
+passwordHash|String|Hash Argon2. Nunca la contraseña
+consent|Object|{privacyNoticeVersion, acceptedAt} (CU-01 paso 6)
+security|Object|{failedLoginAttempts, lockedUntil, mfa:{enabled, secretEnc}} (CU-02 E2, CU-03)
+deviceTokens|Array<Object>|Tokens para notificaciones push (CU-06)
createdAt|Date|Creación
updatedAt|Date|Actualización""","email: único | status | roles")

col("roles","identity","CU-08 (RF-03)","Catálogo de roles y permisos por modo.","""
_id|ObjectId|Identificador
+code|String|ciudadano / tecnico_voluntario / inspector / administrador
name|String|Nombre
~permissions|Array<Object>|[{key:'incident:create', modes:['EMERGENCIA']}] (RF-03 pide permisos POR MODO; ver H-02)
active|Boolean|Activo""","code: único")

col("operational_modes","operating_mode","CU-04","Estado global Cotidiano/Emergencia y su historial de cambios.","""
_id|ObjectId|Identificador
mode|String|COTIDIANO / EMERGENCIA
reason|String|Motivo
changedBy|ObjectId|Administrador (usuario)
previousMode|String|Modo anterior
startedAt|Date|Inicio
endedAt|Date/null|Fin
active|Boolean|Vigente
+mfaVerified|Boolean|Si el cambio pasó MFA (RN-07)""","único PARCIAL en {active:true} (solo un modo vigente) | startedAt desc")

col("audit_logs","audit","CU-05 CU-09","Eventos críticos y trazabilidad. Solo se insertan, nunca se editan.","""
_id|ObjectId|Identificador
actorId|ObjectId|Usuario
action|String|Acción
resource|String|Recurso
resourceId|ObjectId|Recurso afectado
result|String|Resultado
createdAt|Date|Fecha
+actorRole|String|Rol al momento de actuar
+mode|String|Modo operacional vigente
+ip|String|Origen
+details|Object|Antes/después u otros datos (sin datos personales innecesarios, RN-05)""","createdAt desc | actorId+createdAt | resource+resourceId")

col("materials","marketplace","CU-11 CU-12 CU-16","Publicaciones de materiales (SegundaVida).","""
_id|ObjectId|Identificador
ownerId|ObjectId|Propietario
title|String|Título
description|String|Descripción
category|String|Categoría
condition|String|Condición
quantity|Number|Cantidad
price|Number|Precio
offerType|String|VENTA / INTERCAMBIO / ALQUILER
location|GeoJSON Point|Ubicación
images|Array<ObjectId>|Imágenes (files)
status|String|Estado
+aidAuthorization|Boolean|El dueño autoriza convertirlo en ayuda en emergencia (O-09)
+moderation|Object|{status, reason, reviewedBy} (CU-16)
+createdAt|Date|Creación""","location: 2dsphere | ownerId | status+category | texto: title+description")

col("tools","marketplace","CU-11 CU-13 CU-14","Herramientas disponibles para alquiler o préstamo.","""
_id|ObjectId|Identificador
ownerId|ObjectId|Propietario
name|String|Nombre
description|String|Descripción
category|String|Categoría
dailyCost|Number|Costo diario
availability|String|Disponibilidad
location|GeoJSON Point|Ubicación
status|String|Estado
+aidAuthorization|Boolean|Autoriza uso como ayuda en emergencia (O-09)
+moderation|Object|{status, reason, reviewedBy}
+createdAt|Date|Creación""","location: 2dsphere | ownerId | status")

col("reservations","marketplace","CU-13 CU-14","Solicitudes de alquiler, fechas, costos y devoluciones.","""
_id|ObjectId|Identificador
toolId|ObjectId|Herramienta
requesterId|ObjectId|Solicitante
startDate|Date|Inicio
endDate|Date|Fin
cost|Number|Costo
status|String|Estado
returnedAt|Date/null|Devolución
+ownerId|ObjectId|Dueño de la herramienta (copiado: CU-14 lista 'mis reservas' sin cruzar colecciones)
+createdAt|Date|Creación""","ownerId+status | requesterId | toolId+startDate+endDate (detectar choques de fechas)")

col("transactions","marketplace","CU-13 CU-15","Operaciones completadas.","""
_id|ObjectId|Identificador
buyerId|ObjectId|Comprador
sellerId|ObjectId|Vendedor
itemId|ObjectId|Elemento
type|String|Tipo
amount|Number|Valor
status|String|Estado
completedAt|Date/null|Finalización
+createdAt|Date|Creación""","buyerId | sellerId")

col("reviews","marketplace","CU-15 CU-16","Calificaciones y comentarios (SegundaVida y OficiosYa).","""
_id|ObjectId|Identificador
transactionId|ObjectId|Transacción
authorId|ObjectId|Autor
targetUserId|ObjectId|Evaluado
rating|Number|Calificación 1-5
comment|String|Comentario
+context|String|MATERIAL / HERRAMIENTA / TECNICO (CU-15 aplica a ambos módulos)
+moderation|Object|{status, reviewedBy} (CU-16)
+createdAt|Date|Creación""","único {transactionId, authorId} | targetUserId")

col("technicians","services","CU-17 CU-18 CU-19 CU-44","Perfil profesional del técnico y su verificación.","""
_id|ObjectId|Identificador
userId|ObjectId|Usuario
specialties|Array<String>|Especialidades
experienceYears|Number|Experiencia
portfolio|Array<ObjectId>|Portafolio (files)
verificationStatus|String|PENDIENTE (por defecto al registrarse) / VERIFICADO / RECHAZADO
availability|Object|Disponibilidad
rating|Number|Valoración
+documents|Array<ObjectId>|Documentos de verificación (CU-17)
+verifiedBy|ObjectId/null|Administrador que verificó (CU-18)
+verifiedAt|Date/null|Fecha de verificación""","userId: único | specialties+verificationStatus")

col("service_requests","services","CU-19 CU-20","Trabajos solicitados por ciudadanos.","""
_id|ObjectId|Identificador
citizenId|ObjectId|Ciudadano
specialty|String|Especialidad
description|String|Descripción
location|GeoJSON Point|Ubicación
status|String|Estado
createdAt|Date|Fecha
+evidenceFiles|Array<ObjectId>|Fotos de evidencia (CU-20)
+updatedAt|Date|Actualización""","location: 2dsphere | citizenId | status")

col("quotes","services","CU-20 CU-21","Propuestas de técnicos y evidencias.","""
_id|ObjectId|Identificador
requestId|ObjectId|Solicitud
technicianId|ObjectId|Técnico
amount|Number|Valor
description|String|Descripción
evidenceFiles|Array<ObjectId>|Evidencias
status|String|Estado
+createdAt|Date|Creación""","requestId | technicianId")

col("wellbeing_surveys","wellbeing","CU-23","Respuestas de bienestar. Deben quedar DESVINCULADAS de la cuenta (RN-03, O-07).","""
_id|ObjectId|Identificador
~respondentId|ObjectId/null|NO guardar el usuario. Ver H-06 y pseudonym
answers|Object|Respuestas
consent|Boolean|Consentimiento
zone|String|Zona agregada
createdAt|Date|Fecha
+pseudonym|String|Hash irreversible (usuario + sal secreta) solo para limitar 1 envío por semana (O-08)
+weekKey|String|Ej. 2026-W41""","único parcial {pseudonym, weekKey} | zone+createdAt")

col("nlp_analysis","wellbeing","CU-25","Resultado del análisis NLP por encuesta.","""
_id|ObjectId|Identificador
surveyId|ObjectId|Encuesta
modelName|String|Modelo
modelVersion|String|Versión
result|Object|Resultado
metrics|Object|Métricas
processedAt|Date|Procesamiento""","surveyId")

col("support_requests","wellbeing","CU-27 CU-28","Solicitudes de orientación con profesionales.","""
_id|ObjectId|Identificador
requesterId|ObjectId|Solicitante
type|String|Tipo
status|String|Estado
assignedProfessionalId|ObjectId/null|Profesional
createdAt|Date|Fecha
+updatedAt|Date|Actualización""","requesterId | status")

col("properties","fieldwork","CU-34","Censo de inmuebles.","""
_id|ObjectId|Identificador
caseId|String|Caso (consecutivo, ver counters)
address|String|Dirección
location|GeoJSON Point|Ubicación
characteristics|Object|Características
residentsCount|Number|Residentes
photos|Array<ObjectId>|Fotos
status|String|Estado
createdBy|ObjectId|Creador
+clientId|String|Id generado en el celular (evita duplicados al sincronizar, CU-37)
+syncedAt|Date/null|Cuándo llegó al servidor
+createdAt|Date|Creación""","caseId: único | clientId: único parcial | location: 2dsphere")

col("property_inspections","fieldwork","CU-35 CU-36 CU-37","Resultados de inspección y habitabilidad.","""
_id|ObjectId|Identificador
propertyId|ObjectId|Inmueble
inspectorId|ObjectId|Inspector
damageLevel|String|Nivel de daño (catálogo)
habitabilityStatus|String|Resultado
findings|String|Hallazgos
evidenceFiles|Array<ObjectId>|Evidencias
protocolVersion|String|Protocolo
inspectedAt|Date|Fecha
+clientId|String|Idempotencia offline (CU-37)
+syncedAt|Date/null|Llegada al servidor
+requiresSecondReview|Boolean|Caso crítico con doble revisión (O-11)
+secondReviewBy|ObjectId/null|Segundo revisor""","propertyId+inspectedAt | clientId: único parcial")

col("incidents","incidents","CU-29 CU-30 CU-32 CU-39","Reportes de emergencia: daño en vivienda, vías bloqueadas, deslizamientos, etc.","""
_id|ObjectId|Identificador
caseId|String|Caso (consecutivo, ver counters)
type|String|VIVIENDA_DANADA / VIA_BLOQUEADA / DESLIZAMIENTO / ...
description|String|Descripción
location|GeoJSON Point|Ubicación
photos|Array<ObjectId>|Fotos (opcionales, O-13)
status|String|Estado (5 estados, catálogo)
priority|String|Prioridad
reportedBy|ObjectId|Reportante
assignedTo|ObjectId/null|Responsable
+severity|String|Gravedad (el documento final la menciona como dato del reporte)
+needs|Array<String>|Necesidades detectadas
+reportedAt|Date|Hora del reporte (en celular, puede ser anterior a createdAt)
+clientId|String|Idempotencia offline (CU-37)
+duplicateOf|ObjectId/null|Reporte principal si es duplicado (problema central del proyecto)
+propertyId|ObjectId/null|Inmueble censado relacionado
+createdAt|Date|Llegada al servidor
+updatedAt|Date|Actualización""","caseId: único | location: 2dsphere | status+priority | reportedBy+createdAt | clientId: único parcial")

col("incident_status_history","incidents","CU-39 (RF-24)","Transiciones de estado y responsables.","""
_id|ObjectId|Identificador
incidentId|ObjectId|Incidente
fromStatus|String|Anterior
toStatus|String|Nuevo
changedBy|ObjectId|Responsable
changedAt|Date|Fecha
+note|String|Motivo o comentario""","incidentId+changedAt")

col("map_layers","geo","CU-10 CU-40","Capas geográficas autorizadas.","""
_id|ObjectId|Identificador
name|String|Nombre
type|String|Tipo
source|String|Fuente
geometry|Object|GeoJSON/Referencia
~visibleForRoles|Array<String>|Códigos de rol (antes ObjectId)
version|String|Versión
updatedAt|Date|Actualización""","name+version")

col("catalogs","geo","CU-10 (RF-20)","Valores configurables: niveles de daño, estados, zonas, categorías.","""
_id|ObjectId|Identificador
name|String|Catálogo
version|String|Versión
items|Array<Object>|Valores
active|Boolean|Activo
updatedAt|Date|Actualización""","name+version: único")

col("donations","aid","CU-33 CU-42","Ofertas de recursos para ayudas.","""
_id|ObjectId|Identificador
donorId|ObjectId|Donante
type|String|Tipo
description|String|Descripción
quantity|Number|Cantidad
location|GeoJSON Point|Ubicación
availableUntil|Date/null|Disponible hasta
status|String|Estado
+createdAt|Date|Creación""","location: 2dsphere | status")

col("aid_needs","aid","CU-31 CU-32 CU-42","Necesidades de ayuda solicitadas (CU-31).","""
_id|ObjectId|Identificador
type|String|Tipo
description|String|Descripción
quantity|Number|Cantidad
location|GeoJSON Point|Ubicación
priority|String|Prioridad
status|String|Estado
+requestedBy|ObjectId|Quien pide la ayuda (CU-32 'mis casos')
+caseId|String|Caso consecutivo
+incidentId|ObjectId/null|Incidente relacionado
+createdAt|Date|Creación""","caseId: único | requestedBy | location: 2dsphere | status+priority")

col("donation_matches","aid","CU-42","Coincidencias entre donaciones y necesidades.","""
_id|ObjectId|Identificador
donationId|ObjectId|Donación
needId|ObjectId|Necesidad
quantity|Number|Cantidad
distance|Number|Distancia (m)
status|String|Estado
assignedAt|Date|Asignación
+assignedBy|ObjectId|Administrador que confirma""","único {donationId, needId} | needId")

col("aid_inventory","aid","CU-41","Recursos disponibles y trazabilidad.","""
_id|ObjectId|Identificador
~sourceId|ObjectId|Origen (antes sourceMaterialId; puede ser material, herramienta o donación)
+sourceType|String|MATERIAL / HERRAMIENTA / DONACION
type|String|Tipo
quantity|Number|Cantidad
availableQuantity|Number|Disponible
status|String|Estado
originTrace|String|Trazabilidad""","sourceType+sourceId | status")

col("volunteers","volunteering","CU-43 CU-44","Perfil de voluntarios.","""
_id|ObjectId|Identificador
userId|ObjectId|Usuario
skills|Array<String>|Habilidades
availability|Object|Disponibilidad
location|GeoJSON Point|Ubicación
certifications|Array<ObjectId>|Certificaciones (files)
authorizationStatus|String|Autorización
+createdAt|Date|Creación""","userId: único | location: 2dsphere | authorizationStatus")

col("assignments","volunteering","CU-38 CU-43","Asignaciones a voluntarios, técnicos e inspectores. (Antes volunteer_assignments; ver H-08)","""
_id|ObjectId|Identificador
~assigneeId|ObjectId|Persona asignada (antes volunteerId)
+assigneeType|String|VOLUNTARIO / TECNICO / INSPECTOR
incidentId|ObjectId/null|Incidente
+propertyId|ObjectId/null|Inmueble a inspeccionar
task|String|Tarea
startDate|Date|Inicio
endDate|Date/null|Fin
status|String|Estado
assignedBy|ObjectId|Asignador""","assigneeId+status | incidentId")

col("notifications","notifications","CU-06 CU-07","Mensajes Push/SMS y estado de envío.","""
_id|ObjectId|Identificador
userId|ObjectId|Destinatario
channel|String|PUSH / SMS
title|String|Título
message|String|Mensaje
zone|String|Zona
status|String|PENDIENTE / ENVIADO / FALLIDO
sentAt|Date/null|Envío
+type|String|CRISIS / ASIGNACION / ...
+attempts|Number|Reintentos (política pendiente, O-16)
+lastError|String/null|Último error
+readAt|Date/null|Lectura (CU-07)
+createdAt|Date|Creación""","userId+readAt | status+createdAt")

col("files","media","CU-47","Metadatos y referencias de fotos, videos y documentos.","""
_id|ObjectId|Identificador
ownerId|ObjectId|Propietario
fileName|String|Nombre
mimeType|String|Tipo MIME
url|String|Referencia segura (no pública)
size|Number|Tamaño
category|String|Categoría
+accessRoles|Array<String>|Roles que pueden verlo (RN-06)
+linkedTo|Object|{collection, id} a qué pertenece
+encrypted|Boolean|Cifrado en reposo (RNF-05)
+retentionUntil|Date/null|Hasta cuándo se conserva (RN-06)
+createdAt|Date|Creación""","ownerId | linkedTo.id | retentionUntil (revisión periódica)")

# ---- colecciones NUEVAS propuestas ----
col("counters","shared","RF-22","NUEVA. Consecutivos para caseId sin duplicados.","""
_id|String|Nombre del contador, ej. incidents-2026
seq|Number|Último número usado (se incrementa con findOneAndUpdate $inc, atómico)""","")
col("sessions","identity","CU-02 A4","NUEVA. Tokens revocables (cerrar sesión, rotación).","""
_id|ObjectId|Identificador
jti|String|Id único del token
userId|ObjectId|Usuario
expiresAt|Date|Vencimiento
revokedAt|Date/null|Revocación""","jti: único | expiresAt: TTL (se borra sola)")
col("password_resets","identity","CU-02 A2","NUEVA. Recuperación de acceso.","""
_id|ObjectId|Identificador
userId|ObjectId|Usuario
tokenHash|String|Hash del enlace/código enviado
expiresAt|Date|Vencimiento
usedAt|Date/null|Uso""","expiresAt: TTL | userId")
col("wellbeing_consents","wellbeing","CU-24","NUEVA. Consentimiento separado de las respuestas (O-07).","""
_id|ObjectId|Identificador
userId|ObjectId|Usuario
privacyNoticeVersion|String|Versión aceptada
grantedAt|Date|Otorgado
revokedAt|Date/null|Revocado""","userId+grantedAt")
col("wellbeing_indicators","wellbeing","CU-26 CU-45","NUEVA. Indicadores agregados por zona (nunca datos individuales, RN-03).","""
_id|ObjectId|Identificador
zone|String|Zona
weekKey|String|Semana
responses|Number|Nº de respuestas (si < umbral mínimo, no se publica; umbral pendiente en O-16)
scores|Object|Promedios por dimensión
themes|Array<Object>|Temas frecuentes del NLP
computedAt|Date|Cálculo""","único {zone, weekKey}")

docs_root = Path(__file__).resolve().parents[2] / "docs"
out = docs_root / "db" if (docs_root / "cu").exists() else Path("docs/db")
out.mkdir(parents=True, exist_ok=True)
index = ["# Índice de colecciones MongoDB (doc 09 + ajustes)\n",
         "Marcas: `+` campo agregado · `~` campo cambiado · sin marca = como el doc 09. "
         "Ajustes explicados en `docs/09_rectificacion_bd_mongodb.md`.\n",
         "| Colección | Contexto | Casos de uso |\n|---|---|---|"]
for name, ctx, cus, purpose, fields, idx in C:
    rows = ["| Campo | Tipo | Descripción |", "|---|---|---|"]
    for line in fields.splitlines():
        f, t, d = line.split("|", 2)
        rows.append(f"| `{f}` | {t} | {d} |")
    md = (f"# Colección `{name}`\n\n- **Contexto:** `{ctx}`\n- **Casos de uso:** {cus}\n"
          f"- **Para qué sirve:** {purpose}\n- **Índices:** {idx or '—'}\n\n" + "\n".join(rows) + "\n")
    (out / f"{name}.md").write_text(md, encoding="utf-8")
    index.append(f"| `{name}` | {ctx} | {cus} |")
(out / "_indice.md").write_text("\n".join(index) + "\n", encoding="utf-8")
print(len(C), "colecciones documentadas")
