# Colección `wellbeing_surveys`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-23
- **Para qué sirve:** Respuestas de bienestar. Deben quedar DESVINCULADAS de la cuenta (RN-03, O-07).
- **Índices:** único parcial {pseudonym, weekKey} | zone+createdAt

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `~respondentId` | ObjectId/null | NO guardar el usuario. Ver H-06 y pseudonym |
| `answers` | Object | Respuestas |
| `consent` | Boolean | Consentimiento |
| `zone` | String | Zona agregada |
| `createdAt` | Date | Fecha |
| `+pseudonym` | String | Hash irreversible (usuario + sal secreta) solo para limitar 1 envío por semana (O-08) |
| `+weekKey` | String | Ej. 2026-W41 |
