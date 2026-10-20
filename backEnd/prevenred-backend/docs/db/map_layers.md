# Colección `map_layers`

- **Contexto:** `geo`
- **Casos de uso:** CU-10 CU-40
- **Para qué sirve:** Capas geográficas autorizadas.
- **Índices:** name+version

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `name` | String | Nombre |
| `type` | String | Tipo |
| `source` | String | Fuente |
| `geometry` | Object | GeoJSON/Referencia |
| `~visibleForRoles` | Array<String> | Códigos de rol (antes ObjectId) |
| `version` | String | Versión |
| `updatedAt` | Date | Actualización |
