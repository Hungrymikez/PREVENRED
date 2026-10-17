# Colección `donation_matches`

- **Contexto:** `aid`
- **Casos de uso:** CU-42
- **Para qué sirve:** Coincidencias entre donaciones y necesidades.
- **Índices:** único {donationId, needId} | needId

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `donationId` | ObjectId | Donación |
| `needId` | ObjectId | Necesidad |
| `quantity` | Number | Cantidad |
| `distance` | Number | Distancia (m) |
| `status` | String | Estado |
| `assignedAt` | Date | Asignación |
| `+assignedBy` | ObjectId | Administrador que confirma |
