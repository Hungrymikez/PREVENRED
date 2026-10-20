# Colección `catalogs`

- **Contexto:** `geo`
- **Casos de uso:** CU-10 (RF-20)
- **Para qué sirve:** Valores configurables: niveles de daño, estados, zonas, categorías.
- **Índices:** name+version: único

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `name` | String | Catálogo |
| `version` | String | Versión |
| `items` | Array<Object> | Valores |
| `active` | Boolean | Activo |
| `updatedAt` | Date | Actualización |
