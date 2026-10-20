# Colección `technicians`

- **Contexto:** `services`
- **Casos de uso:** CU-17 CU-18 CU-19 CU-44
- **Para qué sirve:** Perfil profesional del técnico y su verificación.
- **Índices:** userId: único | specialties+verificationStatus

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador |
| `userId` | ObjectId | Usuario |
| `specialties` | Array<String> | Especialidades |
| `experienceYears` | Number | Experiencia |
| `portfolio` | Array<ObjectId> | Portafolio (files) |
| `verificationStatus` | String | PENDIENTE (por defecto al registrarse) / VERIFICADO / RECHAZADO |
| `availability` | Object | Disponibilidad |
| `rating` | Number | Valoración |
| `+documents` | Array<ObjectId> | Documentos de verificación (CU-17) |
| `+verifiedBy` | ObjectId/null | Administrador que verificó (CU-18) |
| `+verifiedAt` | Date/null | Fecha de verificación |
