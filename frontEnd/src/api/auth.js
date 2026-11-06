import { api } from '@/api/client'

/** CU-01. Roles permitidos: "ciudadano" o "tecnico_voluntario". */
export async function registrar(datos) {
  const { data } = await api.post('/auth/register', datos)
  return data // { id, full_name, email, role, neighborhood }
}

/** CU-02. */
export async function iniciarSesion(email, password) {
  const { data } = await api.post('/auth/login', { email, password })
  return data // { access_token, token_type, role }
}

/** Datos del usuario dueño del token actual. */
export async function obtenerUsuarioActual() {
  const { data } = await api.get('/auth/me')
  return data // { id, full_name, email, role, neighborhood }
}
