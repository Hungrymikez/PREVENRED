# Colección `tools`

- **Contexto:** `marketplace`
- **Casos de uso:** CU-11 CU-13 CU-14
- **Para qué sirve:** Herramientas disponibles para alquiler o préstamo.
- **Índices:** location: 2dsphere | ownerId | status

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `ownerId` | ObjectId | Propietario |
| `name` | String | Nombre |
| `description` | String | Descripción |
| `category` | String | Categoría |
| `dailyCost` | Number | Costo diario |
| `availability` | String | Disponibilidad |
| `location` | GeoJSON Point | Ubicación |
| `status` | String | Estado |
| `+aidAuthorization` | Boolean | Autoriza uso como ayuda en emergencia (O-09) |
| `+moderation` | Object | {status, reason, reviewedBy} |
| `+createdAt` | Date | Creación |
