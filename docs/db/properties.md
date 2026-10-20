# Colección `properties`

- **Contexto:** `fieldwork`
- **Casos de uso:** CU-34
- **Para qué sirve:** Censo de inmuebles.
- **Índices:** caseId: único | clientId: único parcial | location: 2dsphere

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `caseId` | String | Caso (consecutivo, ver counters) |
| `address` | String | Dirección |
| `location` | GeoJSON Point | Ubicación |
| `characteristics` | Object | Características |
| `residentsCount` | Number | Residentes |
| `photos` | Array<ObjectId> | Fotos |
| `status` | String | Estado |
| `createdBy` | ObjectId | Creador |
| `+clientId` | String | Id generado en el celular (evita duplicados al sincronizar, CU-37) |
| `+syncedAt` | Date/null | Cuándo llegó al servidor |
| `+createdAt` | Date | Creación |
