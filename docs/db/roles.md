# Colección `roles`

- **Contexto:** `identity`
- **Casos de uso:** CU-08 (RF-03)
- **Para qué sirve:** Catálogo de roles y permisos por modo.
- **Índices:** code: único

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `+code` | String | ciudadano / tecnico_voluntario / inspector / administrador |
| `name` | String | Nombre |
| `~permissions` | Array<Object> | [{key:'incident:create', modes:['EMERGENCIA']}] (RF-03 pide permisos POR MODO; ver H-02) |
| `active` | Boolean | Activo |
