import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listarInspecciones, registrarInspeccion } from '@/api/inspecciones'
import { renderConApp } from '@/test/utils'
import Inspecciones from './Inspecciones'
import NuevaInspeccion from './NuevaInspeccion'

vi.mock('@/api/inspecciones', async (original) => ({
  ...(await original()),
  listarInspecciones: vi.fn(),
  registrarInspeccion: vi.fn(),
}))

// El mapa real (Leaflet) no funciona en el navegador simulado: se reemplaza por un botón.
vi.mock('@/components/mapa/SelectorUbicacion', () => ({
  SelectorUbicacion: ({ valor, onCambiar, error }) => (
    <>
      <button type="button" onClick={() => onCambiar([4.82, -75.67])}>
        Marcar en el mapa
      </button>
      {valor && <p>Punto: {valor.join(', ')}</p>}
      {error && <p>{error}</p>}
    </>
  ),
}))

const INSPECTOR = { id: 'u9', full_name: 'Inspector', role: 'inspector' }

const INSPECCION = {
  id: 'i1',
  property_address: 'Calle 14 # 9-30',
  neighborhood: 'Cuba',
  residents_count: 3,
  damage_level: 'SEVERO',
  habitability: 'EVACUACION',
  technical_notes: 'Grietas en muro de carga',
  longitude: -75.71,
  latitude: 4.79,
  inspector_id: 'u9',
  photos: [],
  created_at: '2026-11-16T10:00:00Z',
}

describe('Inspecciones (CU-35)', () => {
  beforeEach(() => listarInspecciones.mockReset())

  it('lista las inspecciones con daño y habitabilidad', async () => {
    listarInspecciones.mockResolvedValue([INSPECCION])
    renderConApp(<Inspecciones />, { auth: { usuario: INSPECTOR } })

    const tarjeta = (await screen.findByText('Calle 14 # 9-30')).closest('article')
    expect(within(tarjeta).getByText('Daño severo')).toBeInTheDocument()
    expect(within(tarjeta).getByText('Evacuación')).toBeInTheDocument()
    expect(within(tarjeta).getByText('3 residentes')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Nueva inspección/ })).toHaveAttribute(
      'href',
      '/inspecciones/nueva',
    )
  })

  it('muestra el estado vacío', async () => {
    listarInspecciones.mockResolvedValue([])
    renderConApp(<Inspecciones />, { auth: { usuario: INSPECTOR } })
    expect(await screen.findByText('Aún no hay inspecciones')).toBeInTheDocument()
  })
})

describe('NuevaInspeccion (CU-34, CU-36)', () => {
  beforeEach(() => registrarInspeccion.mockReset())

  it('valida los campos obligatorios antes de enviar', async () => {
    const usuario = userEvent.setup()
    renderConApp(<NuevaInspeccion />, { auth: { usuario: INSPECTOR } })

    await usuario.click(screen.getByRole('button', { name: 'Registrar inspección' }))

    expect(screen.getByText('Escribe la dirección completa.')).toBeInTheDocument()
    expect(screen.getByText('Marca la ubicación del inmueble.')).toBeInTheDocument()
    expect(registrarInspeccion).not.toHaveBeenCalled()
  })

  it('registra la inspección de un caso con la ubicación recibida', async () => {
    const usuario = userEvent.setup()
    registrarInspeccion.mockResolvedValue(INSPECCION)
    renderConApp(<NuevaInspeccion />, {
      auth: { usuario: INSPECTOR },
      ruta: '/inspecciones/nueva?caso=c1&lat=4.79&lon=-75.71',
    })

    expect(screen.getByText('Inspección relacionada con el caso c1.')).toBeInTheDocument()
    expect(screen.getByText('Punto: 4.79, -75.71')).toBeInTheDocument()

    await usuario.type(screen.getByLabelText('Dirección del inmueble'), 'Calle 14 # 9-30')
    await usuario.type(screen.getByLabelText('Barrio o comuna'), 'Cuba')
    await usuario.type(screen.getByLabelText('Número de residentes'), '3')
    await usuario.selectOptions(screen.getByLabelText('Nivel de daño'), 'SEVERO')
    await usuario.selectOptions(screen.getByLabelText('Habitabilidad'), 'EVACUACION')
    await usuario.type(screen.getByLabelText(/Hallazgos técnicos/), 'Grietas')
    await usuario.click(screen.getByRole('button', { name: 'Registrar inspección' }))

    expect(registrarInspeccion).toHaveBeenCalledWith({
      direccion: 'Calle 14 # 9-30',
      barrio: 'Cuba',
      residentes: '3',
      nivelDano: 'SEVERO',
      habitabilidad: 'EVACUACION',
      notas: 'Grietas',
      ubicacion: [4.79, -75.71],
      caso: 'c1',
    })
    expect(await screen.findByText(/Inspección registrada/)).toBeInTheDocument()
  })
})
