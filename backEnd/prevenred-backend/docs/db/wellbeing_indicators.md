# Colección `wellbeing_indicators`

- **Contexto:** `wellbeing`
- **Casos de uso:** CU-26 CU-45
- **Para qué sirve:** NUEVA. Indicadores agregados por zona (nunca datos individuales, RN-03).
- **Índices:** único {zone, weekKey}

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `zone` | String | Zona |
| `weekKey` | String | Semana |
| `responses` | Number | Nº de respuestas (si < umbral mínimo, no se publica; umbral pendiente en O-16) |
| `scores` | Object | Promedios por dimensión |
| `themes` | Array<Object> | Temas frecuentes del NLP |
| `computedAt` | Date | Cálculo |
