# Colección `files`

- **Contexto:** `media`
- **Casos de uso:** CU-47
- **Para qué sirve:** Metadatos y referencias de fotos, videos y documentos.
- **Índices:** ownerId | linkedTo.id | retentionUntil (revisión periódica)

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `ownerId` | ObjectId | Propietario |
| `fileName` | String | Nombre |
| `mimeType` | String | Tipo MIME |
| `url` | String | Referencia segura (no pública) |
| `size` | Number | Tamaño |
| `category` | String | Categoría |
| `+accessRoles` | Array<String> | Roles que pueden verlo (RN-06) |
| `+linkedTo` | Object | {collection, id} a qué pertenece |
| `+encrypted` | Boolean | Cifrado en reposo (RNF-05) |
| `+retentionUntil` | Date/null | Hasta cuándo se conserva (RN-06) |
| `+createdAt` | Date | Creación |
