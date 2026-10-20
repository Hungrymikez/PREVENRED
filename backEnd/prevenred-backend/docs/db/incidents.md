# Colección `incidents`

- **Contexto:** `incidents`
- **Casos de uso:** CU-29 CU-30 CU-32 CU-39
- **Para qué sirve:** Reportes de emergencia: daño en vivienda, vías bloqueadas, deslizamientos, etc.
- **Índices:** caseId: único | location: 2dsphere | status+priority | reportedBy+createdAt | clientId: único parcial

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `caseId` | String | Caso (consecutivo, ver counters) |
| `type` | String | VIVIENDA_DANADA / VIA_BLOQUEADA / DESLIZAMIENTO / ... |
| `description` | String | Descripción |
| `location` | GeoJSON Point | Ubicación |
| `photos` | Array<ObjectId> | Fotos (opcionales, O-13) |
| `status` | String | Estado (5 estados, catálogo) |
| `priority` | String | Prioridad |
| `reportedBy` | ObjectId | Reportante |
| `assignedTo` | ObjectId/null | Responsable |
| `+severity` | String | Gravedad (el documento final la menciona como dato del reporte) |
| `+needs` | Array<String> | Necesidades detectadas |
| `+reportedAt` | Date | Hora del reporte (en celular, puede ser anterior a createdAt) |
| `+clientId` | String | Idempotencia offline (CU-37) |
| `+duplicateOf` | ObjectId/null | Reporte principal si es duplicado (problema central del proyecto) |
| `+propertyId` | ObjectId/null | Inmueble censado relacionado |
| `+createdAt` | Date | Llegada al servidor |
| `+updatedAt` | Date | Actualización |
