import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listarTecnicos } from '@/api/oficiosya'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import OficiosYa from './OficiosYa'

vi.mock('@/api/oficiosya', async (original) => ({
  ...(await original()),
  listarTecnicos: vi.fn(),
}))

const TECNICO = {
  id: 't1',
  full_name: 'Carlos Arango',
  specialties: ['PLOMERIA', 'ELECTRICIDAD'],
  experience_years: 5,
  bio: '',
  verification_status: 'VERIFICADO',
  rating_average: 4.5,
  reviews_count: 2,
  coordenadas: [4.796, -75.731],
  zona: 'Cuba',
}

describe('OficiosYa (CU-19)', () => {
  beforeEach(() => listarTecnicos.mockReset())

  it('muestra los técnicos del backend con sus oficios y barrio aproximado', async () => {
    listarTecnicos.mockResolvedValue([TECNICO])
    renderConApp(<OficiosYa />, { auth: { usuario: USUARIO_PRUEBA }, ruta: '/oficiosya' })

    const tarjeta = (await screen.findByText('Carlos Arango')).closest('a')
    expect(tarjeta).toHaveAttribute('href', '/oficiosya/t1')
    expect(within(tarjeta).getByText('Plomería')).toBeInTheDocument()
    expect(within(tarjeta).getByText('Electricidad')).toBeInTheDocument()
    expect(within(tarjeta).getByText('Cerca de Cuba')).toBeInTheDocument()
  })

  it('pide al backend la especialidad elegida (código del enum)', async () => {
    listarTecnicos.mockResolvedValue([])
    renderConApp(<OficiosYa />, { auth: { usuario: USUARIO_PRUEBA }, ruta: '/oficiosya' })
    await screen.findByText('Sin resultados')

    await userEvent.selectOptions(screen.getByLabelText('Especialidad'), 'Pintura')
    expect(listarTecnicos).toHaveBeenLastCalledWith({ especialidad: 'PINTURA' })
  })
})
