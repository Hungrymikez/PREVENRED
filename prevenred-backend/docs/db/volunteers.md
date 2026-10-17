# Colección `volunteers`

- **Contexto:** `volunteering`
- **Casos de uso:** CU-43 CU-44
- **Para qué sirve:** Perfil de voluntarios.
- **Índices:** userId: único | location: 2dsphere | authorizationStatus

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `userId` | ObjectId | Usuario |
| `skills` | Array<String> | Habilidades |
| `availability` | Object | Disponibilidad |
| `location` | GeoJSON Point | Ubicación |
| `certifications` | Array<ObjectId> | Certificaciones (files) |
| `authorizationStatus` | String | Autorización |
| `+createdAt` | Date | Creación |
