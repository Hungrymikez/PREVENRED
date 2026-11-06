import { Navigate, Outlet, useLocation } from 'react-router'
import { PantallaCarga } from '@/components/ui/PantallaCarga'
import { useAuth } from '@/hooks/useAuth'

/**
 * Solo deja pasar a usuarios con sesión. Si se indican `roles`, además exige uno de ellos.
 * Uso: <Route element={<RutaProtegida roles={[ROLES.ADMINISTRADOR]} />}> ...rutas... </Route>
 */
export function RutaProtegida({ roles }) {
  const { usuario, verificando } = useAuth()
  const ubicacion = useLocation()

  if (verificando) return <PantallaCarga />
  // Se guarda a dónde quería ir para devolverlo ahí después del login.
  if (!usuario) return <Navigate to="/login" replace state={{ desde: ubicacion }} />
  if (roles && !roles.includes(usuario.role)) return <Navigate to="/sin-permiso" replace />

  return <Outlet />
}

/** Para login y registro: si ya hay sesión, manda al panel. */
export function RutaPublica() {
  const { usuario, verificando } = useAuth()

  if (verificando) return <PantallaCarga />
  if (usuario) return <Navigate to="/panel" replace />

  return <Outlet />
}
