# Colección `quotes`

- **Contexto:** `services`
- **Casos de uso:** CU-20 CU-21
- **Para qué sirve:** Propuestas de técnicos y evidencias.
- **Índices:** requestId | technicianId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `requestId` | ObjectId | Solicitud |
| `technicianId` | ObjectId | Técnico |
| `amount` | Number | Valor |
| `description` | String | Descripción |
| `evidenceFiles` | Array<ObjectId> | Evidencias |
| `status` | String | Estado |
| `+createdAt` | Date | Creación |
