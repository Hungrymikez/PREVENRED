# Colección `notifications`

- **Contexto:** `notifications`
- **Casos de uso:** CU-06 CU-07
- **Para qué sirve:** Mensajes Push/SMS y estado de envío.
- **Índices:** userId+readAt | status+createdAt

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `userId` | ObjectId | Destinatario |
| `channel` | String | PUSH / SMS |
| `title` | String | Título |
| `message` | String | Mensaje |
| `zone` | String | Zona |
| `status` | String | PENDIENTE / ENVIADO / FALLIDO |
| `sentAt` | Date/null | Envío |
| `+type` | String | CRISIS / ASIGNACION / ... |
| `+attempts` | Number | Reintentos (política pendiente, O-16) |
| `+lastError` | String/null | Último error |
| `+readAt` | Date/null | Lectura (CU-07) |
| `+createdAt` | Date | Creación |
