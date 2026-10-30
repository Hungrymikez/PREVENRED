import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import Reportar from './Reportar'

// El mapa real (Leaflet) no funciona en el navegador simulado: se reemplaza por un botón.
vi.mock('@/components/mapa/SelectorUbicacion', () => ({
  SelectorUbicacion: ({ onCambiar, error }) => (
    <>
      <button type="button" onClick={() => onCambiar([4.82, -75.67])}>
        Marcar en el mapa
      </button>
      {error && <p>{error}</p>}
    </>
  ),
}))

function abrir(categoria) {
  renderConApp(
    <Routes>
      <Route path="/emergencia/reportar/:categoria" element={<Reportar />} />
    </Routes>,
    { auth: { usuario: USUARIO_PRUEBA }, ruta: `/emergencia/reportar/${categoria}` },
  )
}

const siguiente = () => userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

describe('Reportar (CU-30)', () => {
  it('reporta un deslizamiento en 3 pasos y entrega el número de caso', async () => {
    abrir('via')

    await siguiente()
    expect(screen.getByText('Elige qué pasó.')).toBeInTheDocument()

    await userEvent.click(screen.getByLabelText('Deslizamiento'))
    await siguiente() // paso 2: foto y descripción son opcionales
    await siguiente()

    await userEvent.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(screen.getByText(/usa el GPS o toca el mapa/i)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Marcar en el mapa' }))
    await userEvent.click(screen.getByRole('button', { name: 'Enviar reporte' }))

    expect(await screen.findByText('Reporte enviado')).toBeInTheDocument()
    expect(screen.getByText(/^PR-2026-\d{5}$/)).toBeInTheDocument()
  })

  it('pide descripción cuando el tipo es "otro"', async () => {
    abrir('via')
    await userEvent.click(screen.getByLabelText('Otro incidente'))
    await siguiente()
    await siguiente()
    expect(screen.getByText('Cuéntanos en pocas palabras qué pasa.')).toBeInTheDocument()
  })
})

describe('Pedir ayuda (CU-31)', () => {
  it('pide el número de personas', async () => {
    abrir('ayuda')
    await userEvent.click(screen.getByLabelText('Agua'))
    await userEvent.clear(screen.getByLabelText('¿Para cuántas personas?'))
    await siguiente()
    expect(screen.getByText('Indica al menos 1 persona.')).toBeInTheDocument()
  })
})
