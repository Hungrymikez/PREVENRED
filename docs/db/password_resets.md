# Colección `password_resets`

- **Contexto:** `identity`
- **Casos de uso:** CU-02 A2
- **Para qué sirve:** NUEVA. Recuperación de acceso.
- **Índices:** expiresAt: TTL | userId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `userId` | ObjectId | Usuario |
| `tokenHash` | String | Hash del enlace/código enviado |
| `expiresAt` | Date | Vencimiento |
| `usedAt` | Date/null | Uso |
