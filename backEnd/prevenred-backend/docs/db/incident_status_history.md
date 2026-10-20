# Colección `incident_status_history`

- **Contexto:** `incidents`
- **Casos de uso:** CU-39 (RF-24)
- **Para qué sirve:** Transiciones de estado y responsables.
- **Índices:** incidentId+changedAt

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `incidentId` | ObjectId | Incidente |
| `fromStatus` | String | Anterior |
| `toStatus` | String | Nuevo |
| `changedBy` | ObjectId | Responsable |
| `changedAt` | Date | Fecha |
| `+note` | String | Motivo o comentario |
