# Colección `property_inspections`

- **Contexto:** `fieldwork`
- **Casos de uso:** CU-35 CU-36 CU-37
- **Para qué sirve:** Resultados de inspección y habitabilidad.
- **Índices:** propertyId+inspectedAt | clientId: único parcial

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `propertyId` | ObjectId | Inmueble |
| `inspectorId` | ObjectId | Inspector |
| `damageLevel` | String | Nivel de daño (catálogo) |
| `habitabilityStatus` | String | Resultado |
| `findings` | String | Hallazgos |
| `evidenceFiles` | Array<ObjectId> | Evidencias |
| `protocolVersion` | String | Protocolo |
| `inspectedAt` | Date | Fecha |
| `+clientId` | String | Idempotencia offline (CU-37) |
| `+syncedAt` | Date/null | Llegada al servidor |
| `+requiresSecondReview` | Boolean | Caso crítico con doble revisión (O-11) |
| `+secondReviewBy` | ObjectId/null | Segundo revisor |
