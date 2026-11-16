import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listarAuditoria } from '@/api/admin'
import { renderConApp } from '@/test/utils'
import Auditoria from './Auditoria'

vi.mock('@/api/admin', async (original) => ({
  ...(await original()),
  listarAuditoria: vi.fn(),
}))

const REGISTRO = {
  id: 'l1',
  actor_id: '64b7f0c2a1b2c3d4e5f60718',
  action: 'CAMBIAR_ESTADO',
  resource: 'incidents',
  resource_id: 'INC-2026-00001',
  details: { de: 'REPORTADO', a: 'RESUELTO' },
  created_at: '2026-11-16T10:00:00Z',
}

describe('Auditoría (CU-09)', () => {
  beforeEach(() => {
    listarAuditoria.mockReset()
  })

  it('lista los registros con acción, recurso, responsable y detalle', async () => {
    listarAuditoria.mockResolvedValue([REGISTRO])
    renderConApp(<Auditoria />)

    const fila = (await screen.findByText('CAMBIAR_ESTADO')).closest('tr')
    expect(within(fila).getByText('Incidentes')).toBeInTheDocument()
    expect(within(fila).getByText('INC-2026-00001')).toBeInTheDocument()
    expect(within(fila).getByText('64b7f0c2a1b2c3d4e5f60718')).toBeInTheDocument()
    expect(within(fila).getByText('de:')).toBeInTheDocument()
    expect(listarAuditoria).toHaveBeenCalledWith({ recurso: '', limite: 50 })
  })

  it('filtra por recurso y cambia el límite pidiéndolo al backend', async () => {
    const usuario = userEvent.setup()
    listarAuditoria.mockResolvedValue([])
    renderConApp(<Auditoria />)

    await usuario.click(await screen.findByRole('button', { name: 'Usuarios' }))
    expect(listarAuditoria).toHaveBeenLastCalledWith({ recurso: 'users', limite: 50 })
    expect(
      await screen.findByText('No hay acciones registradas sobre «Usuarios».'),
    ).toBeInTheDocument()

    await usuario.selectOptions(screen.getByLabelText('Mostrar'), '200')
    expect(listarAuditoria).toHaveBeenLastCalledWith({ recurso: 'users', limite: 200 })
  })

  it('muestra el error del backend', async () => {
    listarAuditoria.mockRejectedValue({
      response: { data: { error: { message: 'Solo administradores.' } } },
    })
    renderConApp(<Auditoria />)
    expect(await screen.findByText('Solo administradores.')).toBeInTheDocument()
  })
})
