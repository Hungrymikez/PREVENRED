import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listarPendientes, verificarTecnico } from '@/api/oficiosya'
import { renderConApp } from '@/test/utils'
import VerificarTecnicos from './VerificarTecnicos'

vi.mock('@/api/oficiosya', async (original) => ({
  ...(await original()),
  listarPendientes: vi.fn(),
  verificarTecnico: vi.fn(),
}))

const ADMIN = { id: 'a1', full_name: 'Admin DIGER', role: 'administrador' }

const PENDIENTE = {
  id: 't1',
  full_name: 'Julián Ospina',
  phone_number: '+573101234567',
  specialties: ['CERRAJERIA'],
  experience_years: 3,
  bio: '',
  verification_status: 'PENDIENTE',
  created_at: '2026-11-16T10:00:00Z',
  coordenadas: [4.808, -75.688],
  zona: 'Pinares',
}

describe('VerificarTecnicos (CU-18)', () => {
  beforeEach(() => {
    listarPendientes.mockReset()
    verificarTecnico.mockReset()
  })

  it('lista los perfiles pendientes', async () => {
    listarPendientes.mockResolvedValue([PENDIENTE])
    renderConApp(<VerificarTecnicos />, { auth: { usuario: ADMIN } })

    expect(await screen.findByText('Julián Ospina')).toBeInTheDocument()
    expect(screen.getByText('Cerrajería')).toBeInTheDocument()
    expect(screen.getByText('+573101234567')).toBeInTheDocument()
    expect(screen.getByText('Cerca de Pinares')).toBeInTheDocument()
  })

  it('aprueba un perfil y lo saca de la lista', async () => {
    const usuario = userEvent.setup()
    listarPendientes.mockResolvedValueOnce([PENDIENTE]).mockResolvedValue([])
    verificarTecnico.mockResolvedValue({ ...PENDIENTE, verification_status: 'VERIFICADO' })
    renderConApp(<VerificarTecnicos />, { auth: { usuario: ADMIN } })

    await usuario.click(await screen.findByRole('button', { name: 'Aprobar' }))
    expect(verificarTecnico).toHaveBeenCalledWith('t1', true)
    expect(
      await screen.findByText('El perfil de Julián Ospina quedó verificado.'),
    ).toBeInTheDocument()
    expect(await screen.findByText('No hay perfiles pendientes')).toBeInTheDocument()
  })

  it('pide confirmación antes de rechazar', async () => {
    const usuario = userEvent.setup()
    listarPendientes.mockResolvedValue([PENDIENTE])
    verificarTecnico.mockResolvedValue({ ...PENDIENTE, verification_status: 'RECHAZADO' })
    renderConApp(<VerificarTecnicos />, { auth: { usuario: ADMIN } })

    await usuario.click(await screen.findByRole('button', { name: 'Rechazar' }))
    expect(verificarTecnico).not.toHaveBeenCalled()
    await usuario.click(screen.getByRole('button', { name: 'Sí, rechazar' }))
    expect(verificarTecnico).toHaveBeenCalledWith('t1', false)
  })

  it('muestra un error amable si falla la carga', async () => {
    listarPendientes.mockRejectedValue({
      response: { data: { error: { message: 'Solo administradores pueden revisar.' } } },
    })
    renderConApp(<VerificarTecnicos />, { auth: { usuario: ADMIN } })
    expect(await screen.findByText('Solo administradores pueden revisar.')).toBeInTheDocument()
  })
})
