import { useCallback, useEffect, useMemo, useState } from 'react'
import { iniciarSesion as loginApi, obtenerUsuarioActual } from '@/api/auth'
import { api, TOKEN_KEY } from '@/api/client'
import { AuthContext } from '@/context/auth-context'

// Datos públicos del último usuario (los de /auth/me), para abrir la app sin conexión.
const USUARIO_KEY = 'prevenred_usuario'

function leer(clave) {
  try {
    return localStorage.getItem(clave)
  } catch {
    return null
  }
}

function leerUsuarioGuardado() {
  try {
    return JSON.parse(leer(USUARIO_KEY))
  } catch {
    return null
  }
}

function recordarUsuario(datos) {
  try {
    localStorage.setItem(USUARIO_KEY, JSON.stringify(datos))
  } catch {
    // Sin almacenamiento: solo se pierde poder abrir la app sin conexión.
  }
}

/**
 * Guarda quién inició sesión y lo comparte con toda la app.
 * Al abrir la app, si hay un token guardado, pide al backend los datos del usuario.
 */
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Mientras se verifica el token guardado no sabemos si hay sesión: las rutas esperan.
  const [verificando, setVerificando] = useState(() => Boolean(leer(TOKEN_KEY)))

  const cerrarSesion = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USUARIO_KEY)
    setUsuario(null)
  }, [])

  useEffect(() => {
    if (!leer(TOKEN_KEY)) return
    obtenerUsuarioActual()
      .then((datos) => {
        recordarUsuario(datos)
        setUsuario(datos)
      })
      .catch((error) => {
        // Sin red no se cierra la sesión: se usa el último usuario conocido para poder
        // reportar sin conexión (CU-37). Si el servidor rechaza el token, sí se cierra.
        const guardado = leerUsuarioGuardado()
        if (!error?.response && guardado) setUsuario(guardado)
        else cerrarSesion()
      })
      .finally(() => setVerificando(false))
  }, [cerrarSesion])

  // Si el backend responde 401 (token vencido o inválido), se cierra la sesión.
  // Los reportes guardados sin conexión se conservan (CU-37 E3).
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
    recordarUsuario(datos)
    setUsuario(datos)
    return datos
  }, [])

  const valor = useMemo(
    () => ({ usuario, verificando, iniciarSesion, cerrarSesion }),
    [usuario, verificando, iniciarSesion, cerrarSesion],
  )

  return <AuthContext value={valor}>{children}</AuthContext>
}
