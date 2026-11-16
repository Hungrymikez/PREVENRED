import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asignarCaso, cambiarEstadoCaso, listarCasos, listarInspectores } from '@/api/casos'
import { renderConApp } from '@/test/utils'
import BandejaCasos from './BandejaCasos'

vi.mock('@/api/casos', async (original) => ({
  ...(await original()),
  listarCasos: vi.fn(),
  cambiarEstadoCaso: vi.fn(),
  asignarCaso: vi.fn(),
  listarInspectores: vi.fn(),
}))

const ADMIN = {
  id: 'adm',
  full_name: 'Coordinador DIGER',
  role: 'administrador',
  neighborhood: 'Centro',
}
const INSPECTOR = {
  id: 'ins1',
  full_name: 'Ingeniero Pereira',
  role: 'inspector',
  neighborhood: 'Cuba',
}

const CASO = {
  id: 'c1',
  case_number: 'INC-2026-00001',
  incident_type: 'VIA_BLOQUEADA',
  severity: 'ALTA',
  status: 'REPORTADO',
  description: 'Árbol caído sobre la vía principal',
  longitude: -75.69,
  latitude: 4.81,
  created_at: '2026-11-16T10:00:00',
  assigned_to: null,
}

function abrir(usuario) {
  renderConApp(<BandejaCasos />, { auth: { usuario } })
}

describe('BandejaCasos (CU-39)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listarInspectores.mockResolvedValue([{ id: 'ins1', full_name: 'Ingeniero Pereira' }])
  })

  it('el administrador ve el caso sin asignar y lo asigna a un inspector', async () => {
    const usuario = userEvent.setup()
    listarCasos.mockResolvedValue([CASO])
    asignarCaso.mockResolvedValue({ ...CASO, status: 'ASIGNADO', assigned_to: 'ins1' })
    abrir(ADMIN)

    const tarjeta = (await screen.findByText('INC-2026-00001')).closest('article')
    expect(within(tarjeta).getByText('Sin asignar')).toBeInTheDocument()
    expect(within(tarjeta).getByText('Gravedad alta')).toBeInTheDocument()

    await usuario.click(within(tarjeta).getByRole('button', { name: 'Asignar inspector' }))
    await usuario.type(screen.getByLabelText('Indicaciones (opcional)'), 'Prioridad alta')
    await usuario.click(screen.getByRole('button', { name: 'Asignar' }))

    expect(asignarCaso).toHaveBeenCalledWith('c1', {
      inspectorId: 'ins1',
      notas: 'Prioridad alta',
    })
    expect(listarCasos).toHaveBeenCalledWith({ estado: '', asignadosAMi: false })
  })

  it('el administrador ve el nombre del responsable y puede cambiar el estado', async () => {
    listarCasos.mockResolvedValue([{ ...CASO, status: 'ASIGNADO', assigned_to: 'ins1' }])
    abrir(ADMIN)
    expect(await screen.findByText('Asignado a Ingeniero Pereira')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reasignar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cambiar estado' })).toBeInTheDocument()
  })

  it('el inspector ve primero sus casos y solo cambia el estado de los suyos', async () => {
    const usuario = userEvent.setup()
    listarCasos.mockResolvedValue([
      { ...CASO, status: 'ASIGNADO', assigned_to: 'ins1' },
      { ...CASO, id: 'c2', case_number: 'INC-2026-00002', assigned_to: 'otro' },
    ])
    cambiarEstadoCaso.mockResolvedValue({})
    abrir(INSPECTOR)

    expect(listarCasos).toHaveBeenCalledWith({ estado: '', asignadosAMi: true })
    const mio = (await screen.findByText('INC-2026-00001')).closest('article')
    const ajeno = screen.getByText('INC-2026-00002').closest('article')
    expect(within(mio).getByText('Asignado a ti')).toBeInTheDocument()
    expect(within(ajeno).queryByRole('button', { name: 'Cambiar estado' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Asignar|Reasignar/ })).not.toBeInTheDocument()
    expect(listarInspectores).not.toHaveBeenCalled()

    await usuario.click(within(mio).getByRole('button', { name: 'Cambiar estado' }))
    await usuario.selectOptions(screen.getByLabelText('Nuevo estado'), 'EN_ATENCION')
    await usuario.type(screen.getByLabelText('Nota (opcional)'), 'Brigada en sitio')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    expect(cambiarEstadoCaso).toHaveBeenCalledWith('c1', {
      estado: 'EN_ATENCION',
      notas: 'Brigada en sitio',
    })
  })

  it('filtra por estado pidiéndolo al backend', async () => {
    const usuario = userEvent.setup()
    listarCasos.mockResolvedValue([])
    abrir(ADMIN)
    await usuario.click(await screen.findByRole('button', { name: 'Resuelto' }))

    expect(listarCasos).toHaveBeenLastCalledWith({ estado: 'RESUELTO', asignadosAMi: false })
    expect(await screen.findByText(/No hay casos en estado «Resuelto»/)).toBeInTheDocument()
  })
})
