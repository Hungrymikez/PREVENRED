# Colección `support_requests`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-27 CU-28
- **Para qué sirve:** Solicitudes de orientación con profesionales.
- **Índices:** requesterId | status

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `requesterId` | ObjectId | Solicitante |
| `type` | String | Tipo |
| `status` | String | Estado |
| `assignedProfessionalId` | ObjectId/null | Profesional |
| `createdAt` | Date | Fecha |
| `+updatedAt` | Date | Actualización |
