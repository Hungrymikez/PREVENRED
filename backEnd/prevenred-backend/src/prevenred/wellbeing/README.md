# Contexto `wellbeing`

- Módulo(s): M08 Mente Resiliente
- Casos de uso: CU-23 CU-24 CU-25 CU-26 CU-27 CU-28
- Colecciones MongoDB: wellbeing_surveys, nlp_analysis, support_requests, wellbeing_consents, wellbeing_indicators
- Fichas: `docs/cu/CU-xx.md` · Colecciones: `docs/db/<coleccion>.md`
- Estado: ⬜ pendiente

## Anonimato (RN-03, O-07/O-08)

- `wellbeing_surveys` **no guarda nada que identifique a la persona**: ni `userId`, ni `respondentId`, ni
  `pseudonym`. Sólo `answers`, `zone`, `triggerEventId` y `createdAt`. No hay índice por persona.
- El límite de **una respuesta por semana** vive en `wellbeing_consents.lastSurveyWeekKey` (`2026-W41`):
  sólo la semana, **nunca la hora**. Se escribe con `record_survey_sent(user_id, purpose, week_key)` y se
  comprueba con `SurveyResponse.was_sent_in(week_key)`.
- El puerto `SurveyRepository` sólo tiene `add` y `count_between`: no existe forma de preguntar por una
  persona desde la encuesta.
- Pruebas: `tests/wellbeing/test_wellbeing.py` (dominio, documento guardado e índices).
