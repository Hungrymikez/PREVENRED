import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router'
import { renderConApp } from '@/test/utils'
import { RutaEmergencia } from './RutaEmergencia'

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
  beforeEach(() => localStorage.clear())

  it('no deja reportar si no hay emergencia activa', async () => {
    abrir()
    expect(await screen.findByText('No hay una emergencia activa')).toBeInTheDocument()
    expect(screen.queryByText('Formulario de reporte')).not.toBeInTheDocument()
  })

  it('deja reportar con el Modo Emergencia activo', async () => {
    localStorage.setItem('prevenred_modo_demo', JSON.stringify({ mode: 'EMERGENCIA' }))
    abrir()
    expect(await screen.findByText('Formulario de reporte')).toBeInTheDocument()
  })
})
