# Colección `nlp_analysis`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-25
- **Para qué sirve:** Resultado del análisis NLP por encuesta.
- **Índices:** surveyId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `surveyId` | ObjectId | Encuesta |
| `modelName` | String | Modelo |
| `modelVersion` | String | Versión |
| `result` | Object | Resultado |
| `metrics` | Object | Métricas |
| `processedAt` | Date | Procesamiento |
