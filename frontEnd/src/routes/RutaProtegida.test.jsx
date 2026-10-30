import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router'
import { renderConApp } from '@/test/utils'
import { RutaProtegida } from './RutaProtegida'

function rutas(roles) {
  return (
    <Routes>
      <Route element={<RutaProtegida roles={roles} />}>
        <Route path="/privado" element={<p>Contenido privado</p>} />
      </Route>
      <Route path="/login" element={<p>Página de login</p>} />
      <Route path="/sin-permiso" element={<p>Sin permiso</p>} />
    </Routes>
  )
}

const ciudadano = { full_name: 'Sara Salas', role: 'ciudadano', neighborhood: 'Cuba' }

describe('RutaProtegida', () => {
  it('manda al login si no hay sesión', () => {
    renderConApp(rutas(), { ruta: '/privado' })
    expect(screen.getByText('Página de login')).toBeInTheDocument()
  })

  it('deja pasar a un usuario con sesión', () => {
    renderConApp(rutas(), { ruta: '/privado', auth: { usuario: ciudadano } })
    expect(screen.getByText('Contenido privado')).toBeInTheDocument()
  })

  it('bloquea a un usuario sin el rol requerido', () => {
    renderConApp(rutas(['administrador']), { ruta: '/privado', auth: { usuario: ciudadano } })
    expect(screen.getByText('Sin permiso')).toBeInTheDocument()
  })

  it('espera mientras se verifica la sesión guardada', () => {
    renderConApp(rutas(), { ruta: '/privado', auth: { verificando: true } })
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
