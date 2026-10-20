# Colección `aid_inventory`

- **Contexto:** `aid`
- **Casos de uso:** CU-41
- **Para qué sirve:** Recursos disponibles y trazabilidad.
- **Índices:** sourceType+sourceId | status

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `~sourceId` | ObjectId | Origen (antes sourceMaterialId; puede ser material, herramienta o donación) |
| `+sourceType` | String | MATERIAL / HERRAMIENTA / DONACION |
| `type` | String | Tipo |
| `quantity` | Number | Cantidad |
| `availableQuantity` | Number | Disponible |
| `status` | String | Estado |
| `originTrace` | String | Trazabilidad |
