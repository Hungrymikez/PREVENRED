# Colección `service_requests`

- **Contexto:** `services`
- **Casos de uso:** CU-19 CU-20
- **Para qué sirve:** Trabajos solicitados por ciudadanos.
- **Índices:** location: 2dsphere | citizenId | status

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `citizenId` | ObjectId | Ciudadano |
| `specialty` | String | Especialidad |
| `description` | String | Descripción |
| `location` | GeoJSON Point | Ubicación |
| `status` | String | Estado |
| `createdAt` | Date | Fecha |
| `+evidenceFiles` | Array<ObjectId> | Fotos de evidencia (CU-20) |
| `+updatedAt` | Date | Actualización |
