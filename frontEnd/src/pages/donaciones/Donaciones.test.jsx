import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  ejecutarEmparejamiento,
  listarMisOfertas,
  listarNecesidadesPendientes,
  listarOfertasPendientes,
  ofrecerAyuda,
} from '@/api/donaciones'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import Donar from './Donar'
import GestionDonaciones from './GestionDonaciones'

vi.mock('@/api/donaciones', async (original) => ({
  ...(await original()),
  ofrecerAyuda: vi.fn(),
  listarMisOfertas: vi.fn(),
  listarNecesidadesPendientes: vi.fn(),
  listarOfertasPendientes: vi.fn(),
  ejecutarEmparejamiento: vi.fn(),
}))
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

const ADMIN = { id: 'u1', full_name: 'Admin', role: 'administrador' }

const OFERTA = {
  id: 'o1',
  title: 'Agua embotellada',
  category: 'AGUA',
  quantity: 60,
  available_quantity: 10,
  unit: 'litros',
  donor_id: 'u1',
  longitude: -75.69,
  latitude: 4.81,
  status: 'PENDIENTE',
  created_at: '2026-11-16T10:00:00Z',
}

const NECESIDAD = {
  id: 'n1',
  title: 'Agua para albergue',
  category: 'AGUA',
  quantity: 50,
  remaining_quantity: 50,
  unit: 'litros',
  priority: 'URGENTE',
  requester_id: 'u3',
  longitude: -75.69,
  latitude: 4.81,
  status: 'PENDIENTE',
  created_at: '2026-11-16T09:00:00Z',
}

describe('Donar (CU-33)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('registra una oferta y lista las propias con lo que queda disponible', async () => {
    const usuario = userEvent.setup()
    listarMisOfertas.mockResolvedValue([OFERTA])
    ofrecerAyuda.mockResolvedValue({ ...OFERTA, id: 'o2', title: 'Arroz' })
    renderConApp(<Donar />, { auth: { usuario: USUARIO_PRUEBA } })

    expect(await screen.findByText('Agua embotellada')).toBeInTheDocument()
    expect(screen.getByText(/Quedan 10 litros disponibles/)).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Ofrecer ayuda' }))
    expect(screen.getByText('Elige una categoría.')).toBeInTheDocument()
    expect(ofrecerAyuda).not.toHaveBeenCalled()

    await usuario.type(screen.getByLabelText('¿Qué donas?'), 'Arroz')
    await usuario.selectOptions(screen.getByLabelText('Categoría'), 'ALIMENTOS')
    await usuario.type(screen.getByLabelText('Cantidad'), '20')
    await usuario.clear(screen.getByLabelText('Unidad'))
    await usuario.type(screen.getByLabelText('Unidad'), 'kg')
    await usuario.click(screen.getByRole('button', { name: 'Marcar en el mapa' }))
    await usuario.click(screen.getByRole('button', { name: 'Ofrecer ayuda' }))

    expect(ofrecerAyuda).toHaveBeenCalledWith({
      titulo: 'Arroz',
      categoria: 'ALIMENTOS',
      cantidad: '20',
      unidad: 'kg',
      ubicacion: [4.82, -75.67],
    })
    expect(await screen.findByText(/Registramos tu oferta «Arroz»/)).toBeInTheDocument()
  })
})

describe('GestionDonaciones (CU-41, CU-42)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('muestra pendientes y los emparejamientos creados', async () => {
    const usuario = userEvent.setup()
    listarNecesidadesPendientes.mockResolvedValue([NECESIDAD])
    listarOfertasPendientes.mockResolvedValue([OFERTA])
    ejecutarEmparejamiento.mockResolvedValue([
      {
        id: 'm1',
        need_id: 'n1',
        offer_id: 'o1',
        matched_quantity: 10,
        distance_meters: 1530,
        matched_by: 'u1',
        matched_at: '2026-11-16T12:00:00Z',
        is_confirmed: true,
      },
    ])
    renderConApp(<GestionDonaciones />, { auth: { usuario: ADMIN } })

    const necesidades = await screen.findByRole('region', { name: 'Necesidades pendientes' })
    expect(await within(necesidades).findByText('Agua para albergue')).toBeInTheDocument()
    expect(within(necesidades).getByText('Urgente')).toBeInTheDocument()
    const ofertas = screen.getByRole('region', { name: 'Donaciones disponibles' })
    expect(await within(ofertas).findByText(/Quedan 10 litros/)).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Ejecutar emparejamiento' }))

    const resultado = await screen.findByRole('region', { name: 'Emparejamientos creados' })
    expect(within(resultado).getByText('Se creó 1 emparejamiento.')).toBeInTheDocument()
    expect(within(resultado).getByText(/10 litros · a 1,5\s+km/)).toBeInTheDocument()
  })

  it('avisa cuando no hay coincidencias', async () => {
    const usuario = userEvent.setup()
    listarNecesidadesPendientes.mockResolvedValue([])
    listarOfertasPendientes.mockResolvedValue([])
    ejecutarEmparejamiento.mockResolvedValue([])
    renderConApp(<GestionDonaciones />, { auth: { usuario: ADMIN } })

    await usuario.click(screen.getByRole('button', { name: 'Ejecutar emparejamiento' }))
    expect(await screen.findByText(/No se encontraron coincidencias/)).toBeInTheDocument()
  })
})
