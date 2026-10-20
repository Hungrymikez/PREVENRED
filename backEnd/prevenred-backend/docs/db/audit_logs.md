# Colección `audit_logs`

- **Contexto:** `audit`
- **Casos de uso:** CU-05 CU-09
- **Para qué sirve:** Eventos críticos y trazabilidad. Solo se insertan, nunca se editan.
- **Índices:** createdAt desc | actorId+createdAt | resource+resourceId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `actorId` | ObjectId | Usuario |
| `action` | String | Acción |
| `resource` | String | Recurso |
| `resourceId` | ObjectId | Recurso afectado |
| `result` | String | Resultado |
| `createdAt` | Date | Fecha |
| `+actorRole` | String | Rol al momento de actuar |
| `+mode` | String | Modo operacional vigente |
| `+ip` | String | Origen |
| `+details` | Object | Antes/después u otros datos (sin datos personales innecesarios, RN-05) |
