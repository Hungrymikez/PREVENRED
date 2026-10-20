# Colección `transactions`

- **Contexto:** `marketplace`
- **Casos de uso:** CU-13 CU-15
- **Para qué sirve:** Operaciones completadas.
- **Índices:** buyerId | sellerId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `buyerId` | ObjectId | Comprador |
| `sellerId` | ObjectId | Vendedor |
| `itemId` | ObjectId | Elemento |
| `type` | String | Tipo |
| `amount` | Number | Valor |
| `status` | String | Estado |
| `completedAt` | Date/null | Finalización |
| `+createdAt` | Date | Creación |
