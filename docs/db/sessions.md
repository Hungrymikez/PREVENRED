# Colección `sessions`

- **Contexto:** `identity`
- **Casos de uso:** CU-02 A4
- **Para qué sirve:** NUEVA. Tokens revocables (cerrar sesión, rotación).
- **Índices:** jti: único | expiresAt: TTL (se borra sola)

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `jti` | String | Id único del token |
| `userId` | ObjectId | Usuario |
| `expiresAt` | Date | Vencimiento |
| `revokedAt` | Date/null | Revocación |
