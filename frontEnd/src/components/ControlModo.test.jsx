import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { cambiarModo, obtenerModo } from '@/api/modo'
import { renderConApp } from '@/test/utils'
import { ControlModo } from './ControlModo'

vi.mock('@/api/modo', () => ({ obtenerModo: vi.fn(), cambiarModo: vi.fn() }))

describe('ControlModo (CU-04)', () => {
  beforeEach(() => {
    localStorage.clear()
    obtenerModo.mockResolvedValue({ mode: 'COTIDIANO' })
    cambiarModo.mockReset()
  })

  it('exige un motivo antes de activar la emergencia', async () => {
    const usuario = userEvent.setup()
    renderConApp(<ControlModo />)
    await usuario.click(await screen.findByRole('button', { name: 'Activar Modo Emergencia' }))
    await usuario.click(screen.getByRole('button', { name: 'Confirmar activación' }))

    expect(screen.getByText(/mínimo 10 caracteres/)).toBeInTheDocument()
    expect(cambiarModo).not.toHaveBeenCalled()
  })

  it('activa la emergencia en el backend con el motivo escrito', async () => {
    const usuario = userEvent.setup()
    cambiarModo.mockResolvedValue({ mode: 'EMERGENCIA', reason: 'Sismo fuerte en Pereira' })
    renderConApp(<ControlModo />)
    await usuario.click(await screen.findByRole('button', { name: 'Activar Modo Emergencia' }))
    await usuario.type(screen.getByLabelText('Motivo de la emergencia'), 'Sismo fuerte en Pereira')
    obtenerModo.mockResolvedValue({ mode: 'EMERGENCIA', reason: 'Sismo fuerte en Pereira' })
    await usuario.click(screen.getByRole('button', { name: 'Confirmar activación' }))

    expect(cambiarModo).toHaveBeenCalledWith({
      activarEmergencia: true,
      motivo: 'Sismo fuerte en Pereira',
    })
    expect(
      await screen.findByRole('button', { name: 'Volver a modo cotidiano' }),
    ).toBeInTheDocument()
  })

  it('muestra el error del backend si no tiene permiso', async () => {
    const usuario = userEvent.setup()
    cambiarModo.mockRejectedValue({
      response: {
        status: 403,
        data: { error: { message: 'No tienes permiso para esta función.' } },
      },
    })
    renderConApp(<ControlModo />)
    await usuario.click(await screen.findByRole('button', { name: 'Activar Modo Emergencia' }))
    await usuario.type(screen.getByLabelText('Motivo de la emergencia'), 'Prueba de permisos')
    await usuario.click(screen.getByRole('button', { name: 'Confirmar activación' }))

    expect(await screen.findByText('No tienes permiso para esta función.')).toBeInTheDocument()
  })
})
