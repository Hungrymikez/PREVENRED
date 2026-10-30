import { useCallback, useEffect, useMemo, useState } from 'react'
import { iniciarSesion as loginApi, obtenerUsuarioActual } from '@/api/auth'
import { api, TOKEN_KEY } from '@/api/client'
import { AuthContext } from '@/context/auth-context'

function leerToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

/**
 * Guarda quién inició sesión y lo comparte con toda la app.
 * Al abrir la app, si hay un token guardado, pide al backend los datos del usuario.
 */
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Mientras se verifica el token guardado no sabemos si hay sesión: las rutas esperan.
  const [verificando, setVerificando] = useState(() => Boolean(leerToken()))

  const cerrarSesion = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUsuario(null)
  }, [])

  useEffect(() => {
    if (!leerToken()) return
    obtenerUsuarioActual()
      .then(setUsuario)
      .catch(cerrarSesion)
      .finally(() => setVerificando(false))
  }, [cerrarSesion])

  // Si el backend responde 401 (token vencido o inválido), se cierra la sesión.
  useEffect(() => {
    const id = api.interceptors.response.use(undefined, (error) => {
      const esLogin = error.config?.url?.includes('/auth/login')
      if (error.response?.status === 401 && !esLogin) cerrarSesion()
      return Promise.reject(error)
    })
    return () => api.interceptors.response.eject(id)
  }, [cerrarSesion])

  const iniciarSesion = useCallback(async (email, password) => {
    const { access_token } = await loginApi(email, password)
    localStorage.setItem(TOKEN_KEY, access_token)
    const datos = await obtenerUsuarioActual()
    setUsuario(datos)
    return datos
  }, [])

  const valor = useMemo(
    () => ({ usuario, verificando, iniciarSesion, cerrarSesion }),
    [usuario, verificando, iniciarSesion, cerrarSesion],
  )

  return <AuthContext value={valor}>{children}</AuthContext>
}
