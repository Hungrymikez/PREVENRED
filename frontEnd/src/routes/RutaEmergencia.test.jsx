import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router'
import { obtenerModo } from '@/api/modo'
import { renderConApp } from '@/test/utils'
import { RutaEmergencia } from './RutaEmergencia'

vi.mock('@/api/modo', () => ({ obtenerModo: vi.fn() }))

function abrir() {
  renderConApp(
    <Routes>
      <Route element={<RutaEmergencia />}>
        <Route path="/emergencia" element={<p>Formulario de reporte</p>} />
      </Route>
    </Routes>,
    { ruta: '/emergencia' },
  )
}

describe('RutaEmergencia (CU-29 E3)', () => {
  beforeEach(() => {
    localStorage.clear()
    obtenerModo.mockResolvedValue({ mode: 'COTIDIANO' })
  })

  it('no deja reportar si no hay emergencia activa', async () => {
    abrir()
    expect(await screen.findByText('No hay una emergencia activa')).toBeInTheDocument()
    expect(screen.queryByText('Formulario de reporte')).not.toBeInTheDocument()
  })

  it('deja reportar con el Modo Emergencia activo', async () => {
    obtenerModo.mockResolvedValue({ mode: 'EMERGENCIA' })
    abrir()
    expect(await screen.findByText('Formulario de reporte')).toBeInTheDocument()
  })
})
