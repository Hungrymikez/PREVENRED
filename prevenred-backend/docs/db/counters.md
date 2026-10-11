# Colección `counters`

- **Contexto:** `shared`
- **Casos de uso:** RF-22
- **Para qué sirve:** NUEVA. Consecutivos para caseId sin duplicados.
- **Índices:** —

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | String | Nombre del contador, ej. incidents-2026 |
| `seq` | Number | Último número usado (se incrementa con findOneAndUpdate $inc, atómico) |
