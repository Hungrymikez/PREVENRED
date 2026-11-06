import { screen, waitForElementToBeRemoved } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import OficiosYa from './OficiosYa'

describe('OficiosYa', () => {
  it('lista técnicos verificados y filtra por especialidad', async () => {
    renderConApp(<OficiosYa />, { auth: { usuario: USUARIO_PRUEBA }, ruta: '/oficiosya' })

    expect(await screen.findByText('Carlos Arango')).toBeInTheDocument()
    expect(screen.queryByText('Julián Ospina')).not.toBeInTheDocument() // pendiente de verificación

    await userEvent.selectOptions(screen.getByLabelText('Especialidad'), 'Pintura')

    // Mientras llega el filtro se ven los resultados anteriores: esperamos a que se actualice.
    await waitForElementToBeRemoved(() => screen.queryByText('Carlos Arango'))
    expect(screen.getByText('Natalia Gómez')).toBeInTheDocument()
  })
})
