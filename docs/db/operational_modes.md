# Colección `operational_modes`

- **Contexto:** `operating_mode`
- **Casos de uso:** CU-04
- **Para qué sirve:** Estado global Cotidiano/Emergencia y su historial de cambios.
- **Índices:** único PARCIAL en {active:true} (solo un modo vigente) | startedAt desc

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `mode` | String | COTIDIANO / EMERGENCIA |
| `reason` | String | Motivo |
| `changedBy` | ObjectId | Administrador (usuario) |
| `previousMode` | String | Modo anterior |
| `startedAt` | Date | Inicio |
| `endedAt` | Date/null | Fin |
| `active` | Boolean | Vigente |
| `+mfaVerified` | Boolean | Si el cambio pasó MFA (RN-07) |
