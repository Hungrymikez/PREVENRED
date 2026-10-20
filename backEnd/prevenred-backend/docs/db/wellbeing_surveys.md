# Colección `wellbeing_surveys`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-23
- **Para qué sirve:** Respuestas de bienestar. Deben quedar DESVINCULADAS de la cuenta (RN-03, O-07).
- **Índices:** zone+createdAt | createdAt. **No hay índice por persona**: el documento es anónimo.
- **Anonimato:** el documento NO tiene `userId`, ni `respondentId`, ni `pseudonym`. El límite de una
  respuesta por semana vive en `wellbeing_consents.lastSurveyWeekKey` (sólo la semana, nunca la hora).

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `answers` | Object | Respuestas de la escala 1-5 |
| `zone` | String/null | Barrio o comuna, para el análisis agregado (CU-23 paso 6) |
| `triggerEventId` | ObjectId/null | Evento que abrió el pulso, si aplica |
| `createdAt` | Date | Fecha de la respuesta |

> Sin campos de identidad: ni `userId`, ni `respondentId`, ni `pseudonym`. Antes existía
> `pseudonym` + `weekKey` y el índice único `uq_surveys_pseudonym_week`; se eliminaron para que la
> encuesta no guarde NINGÚN dato que la vincule a una persona. Una consulta que necesite «cuántas
> respuestas de esta semana» puede contar por `createdAt` sin identificar a nadie.
