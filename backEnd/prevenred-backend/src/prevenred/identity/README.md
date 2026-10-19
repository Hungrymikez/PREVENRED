# Contexto `identity`

- Módulo(s): M01 Acceso, usuarios y roles
- Casos de uso: CU-01 CU-02 CU-03 CU-08
- Colecciones MongoDB: users, roles, sessions, password_resets
- Fichas: `docs/cu/CU-xx.md` · Colecciones: `docs/db/<coleccion>.md`
- Estado: ✅ CU-01 y CU-02 expuestos por HTTP sobre MongoDB (molde de referencia). CU-03, CU-08 y `sessions`/`password_resets` existen como casos de uso/adaptadores pero **sin ruta**: ver `README_API.md` §6 (el login de Administrador responde `500` hoy)
