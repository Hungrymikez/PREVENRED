import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { AuthContext } from '@/context/auth-context'

/**
 * Renderiza un componente con router, caché de datos y una sesión simulada.
 * Ej.: renderConApp(<Login />, { auth: { iniciarSesion: vi.fn() }, ruta: '/login' })
 */
export function renderConApp(ui, { auth = {}, ruta = '/' } = {}) {
  const sesion = {
    usuario: null,
    verificando: false,
    iniciarSesion: vi.fn(),
    cerrarSesion: vi.fn(),
    ...auth,
  }
  // Una caché nueva por prueba, sin reintentos, para que las pruebas no se afecten entre sí.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext value={sesion}>
        <MemoryRouter initialEntries={[ruta]}>{ui}</MemoryRouter>
      </AuthContext>
    </QueryClientProvider>,
  )
}

export const USUARIO_PRUEBA = {
  id: 'u1',
  full_name: 'Sara Salas',
  email: 'sara@correo.com',
  role: 'ciudadano',
  neighborhood: 'Cuba',
}
