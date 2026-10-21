# Colección `users`

- **Contexto:** `identity`
- **Casos de uso:** CU-01 CU-02 CU-03 CU-08 CU-06
- **Para qué sirve:** Identidad, contacto, rol, estado y seguridad de la cuenta.
- **Índices:** email: único | status | roles

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `name` | String | Nombre completo |
| `email` | String | Correo (único, en minúsculas) |
| `phone` | String | Teléfono |
| `~roles` | Array<String> | Códigos de rol (antes Array<ObjectId>; ver H-01) |
| `status` | String | ACTIVE / SUSPENDED |
| `verified` | Boolean | Verificación |
| `location` | Object | Ubicación autorizada. Incluye neighborhood (barrio/comuna) |
| `+passwordHash` | String | Hash Argon2. Nunca la contraseña |
| `+consent` | Object | {privacyNoticeVersion, acceptedAt} (CU-01 paso 6) |
| `+security` | Object | {failedLoginAttempts, lockedUntil, mfa:{enabled, secretEnc}} (CU-02 E2, CU-03) |
| `+deviceTokens` | Array<Object> | Tokens para notificaciones push (CU-06) |
| `createdAt` | Date | Creación |
| `updatedAt` | Date | Actualización |
