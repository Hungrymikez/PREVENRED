# Colección `reservations`

- **Contexto:** `marketplace`
- **Casos de uso:** CU-13 CU-14
- **Para qué sirve:** Solicitudes de alquiler, fechas, costos y devoluciones.
- **Índices:** ownerId+status | requesterId | toolId+startDate+endDate (detectar choques de fechas)

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `toolId` | ObjectId | Herramienta |
| `requesterId` | ObjectId | Solicitante |
| `startDate` | Date | Inicio |
| `endDate` | Date | Fin |
| `cost` | Number | Costo |
| `status` | String | Estado |
| `returnedAt` | Date/null | Devolución |
| `+ownerId` | ObjectId | Dueño de la herramienta (copiado: CU-14 lista 'mis reservas' sin cruzar colecciones) |
| `+createdAt` | Date | Creación |
