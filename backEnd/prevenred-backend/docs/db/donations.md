# Colección `donations`

- **Contexto:** `aid`
- **Casos de uso:** CU-33 CU-42
- **Para qué sirve:** Ofertas de recursos para ayudas.
- **Índices:** location: 2dsphere | status

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `donorId` | ObjectId | Donante |
| `type` | String | Tipo |
| `description` | String | Descripción |
| `quantity` | Number | Cantidad |
| `location` | GeoJSON Point | Ubicación |
| `availableUntil` | Date/null | Disponible hasta |
| `status` | String | Estado |
| `+createdAt` | Date | Creación |
