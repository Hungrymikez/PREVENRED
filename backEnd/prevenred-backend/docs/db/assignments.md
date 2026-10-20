# Colección `assignments`

- **Contexto:** `volunteering`
- **Casos de uso:** CU-38 CU-43
- **Para qué sirve:** Asignaciones a voluntarios, técnicos e inspectores. (Antes volunteer_assignments; ver H-08)
- **Índices:** assigneeId+status | incidentId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `~assigneeId` | ObjectId | Persona asignada (antes volunteerId) |
| `+assigneeType` | String | VOLUNTARIO / TECNICO / INSPECTOR |
| `incidentId` | ObjectId/null | Incidente |
| `+propertyId` | ObjectId/null | Inmueble a inspeccionar |
| `task` | String | Tarea |
| `startDate` | Date | Inicio |
| `endDate` | Date/null | Fin |
| `status` | String | Estado |
| `assignedBy` | ObjectId | Asignador |
