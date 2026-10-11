# Colección `wellbeing_consents`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-24
- **Para qué sirve:** NUEVA. Consentimiento separado de las respuestas (O-07).
- **Índices:** userId+grantedAt

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `userId` | ObjectId | Usuario |
| `privacyNoticeVersion` | String | Versión aceptada |
| `grantedAt` | Date | Otorgado |
| `revokedAt` | Date/null | Revocado |
