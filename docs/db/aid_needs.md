# Colección `aid_needs`

- **Contexto:** `aid`
- **Casos de uso:** CU-31 CU-32 CU-42
- **Para qué sirve:** Necesidades de ayuda solicitadas (CU-31).
- **Índices:** caseId: único | requestedBy | location: 2dsphere | status+priority

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `type` | String | Tipo |
| `description` | String | Descripción |
| `quantity` | Number | Cantidad |
| `location` | GeoJSON Point | Ubicación |
| `priority` | String | Prioridad |
| `status` | String | Estado |
| `+requestedBy` | ObjectId | Quien pide la ayuda (CU-32 'mis casos') |
| `+caseId` | String | Caso consecutivo |
| `+incidentId` | ObjectId/null | Incidente relacionado |
| `+createdAt` | Date | Creación |
