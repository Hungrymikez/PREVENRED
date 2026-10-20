# Colección `reviews`

- **Contexto:** `marketplace`
- **Casos de uso:** CU-15 CU-16
- **Para qué sirve:** Calificaciones y comentarios (SegundaVida y OficiosYa).
- **Índices:** único {transactionId, authorId} | targetUserId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `transactionId` | ObjectId | Transacción |
| `authorId` | ObjectId | Autor |
| `targetUserId` | ObjectId | Evaluado |
| `rating` | Number | Calificación 1-5 |
| `comment` | String | Comentario |
| `+context` | String | MATERIAL / HERRAMIENTA / TECNICO (CU-15 aplica a ambos módulos) |
| `+moderation` | Object | {status, reviewedBy} (CU-16) |
| `+createdAt` | Date | Creación |
