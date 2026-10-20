# Colección `wellbeing_consents`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-24 (y el límite semanal de CU-23)
- **Para qué sirve:** NUEVA. Consentimiento separado de las respuestas (O-07). También guarda la semana
  del último envío de bienestar, porque la encuesta es anónima y no puede llevar ese dato.
- **Índices:** único parcial {userId, purpose} `uq_consent_active` | userId+grantedAt | userId+lastSurveyWeekKey

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `userId` | ObjectId | Usuario |
| `purpose` | String | `ANALITICA_BIENESTAR`, `NOTIFICACIONES`, `UBICACION_PRECISA` |
| `privacyNoticeVersion` | String | Versión aceptada |
| `granted` | Boolean | Vigente |
| `grantedAt` | Date | Otorgado |
| `revokedAt` | Date/null | Revocado |
| `lastSurveyWeekKey` | String/null | Semana ISO del último envío de bienestar (`2026-W41`). **Sólo la semana, nunca la hora** (O-08) |

> `lastSurveyWeekKey` se escribe con `$max`: repetir un envío no cambia el valor y una semana anterior no
> lo retrocede. El campo se **omite** mientras no haya envíos (`$max` no puede comparar texto con `null`).
