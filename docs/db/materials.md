# Colección `materials`

- **Contexto:** `marketplace`
- **Casos de uso:** CU-11 CU-12 CU-16
- **Para qué sirve:** Publicaciones de materiales (SegundaVida).
- **Índices:** location: 2dsphere | ownerId | status+category | texto: title+description

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `ownerId` | ObjectId | Propietario |
| `title` | String | Título |
| `description` | String | Descripción |
| `category` | String | Categoría |
| `condition` | String | Condición |
| `quantity` | Number | Cantidad |
| `price` | Number | Precio |
| `offerType` | String | VENTA / INTERCAMBIO / ALQUILER |
| `location` | GeoJSON Point | Ubicación |
| `images` | Array<ObjectId> | Imágenes (files) |
| `status` | String | Estado |
| `+aidAuthorization` | Boolean | El dueño autoriza convertirlo en ayuda en emergencia (O-09) |
| `+moderation` | Object | {status, reason, reviewedBy} (CU-16) |
| `+createdAt` | Date | Creación |
