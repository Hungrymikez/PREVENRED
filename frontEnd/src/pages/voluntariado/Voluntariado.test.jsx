import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listarCasos } from '@/api/casos'
import {
  asignarVoluntario,
  inscribirVoluntario,
  listarMisAsignaciones,
  listarVoluntarios,
  obtenerMiPerfil,
} from '@/api/voluntariado'
import { renderConApp } from '@/test/utils'
import AsignarVoluntarios from './AsignarVoluntarios'
import Voluntariado from './Voluntariado'

vi.mock('@/api/voluntariado', async (original) => ({
  ...(await original()),
  obtenerMiPerfil: vi.fn(),
  inscribirVoluntario: vi.fn(),
  listarMisAsignaciones: vi.fn(),
  listarVoluntarios: vi.fn(),
  asignarVoluntario: vi.fn(),
}))
vi.mock('@/api/casos', async (original) => ({
  ...(await original()),
  listarCasos: vi.fn(),
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

const TECNICO = { id: 'u2', full_name: 'Laura Rescatista', role: 'tecnico_voluntario' }
const ADMIN = { id: 'u1', full_name: 'Admin', role: 'administrador' }

const PERFIL = {
  id: 'v1',
  user_id: 'u2',
  full_name: 'Laura Rescatista',
  phone_number: '3101234567',
  skills: ['RESCATE', 'PRIMEROS_AUXILIOS'],
  is_available: true,
  longitude: -75.69,
  latitude: 4.81,
  created_at: '2026-11-16T10:00:00Z',
}

const MISION = {
  id: 'a1',
  volunteer_id: 'v1',
  incident_id: '64b7f0c2a1b2c3d4e5f60718',
  task_description: 'Apoyar evacuación del sector',
  status: 'ASIGNADO',
  assigned_by: 'u1',
  created_at: '2026-11-16T11:00:00Z',
}

describe('Voluntariado (CU-44, CU-38)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('inscribe a quien aún no es voluntario', async () => {
    const usuario = userEvent.setup()
    obtenerMiPerfil.mockResolvedValue(null)
    inscribirVoluntario.mockResolvedValue(PERFIL)
    listarMisAsignaciones.mockResolvedValue([])
    renderConApp(<Voluntariado />, { auth: { usuario: TECNICO } })

    expect(await screen.findByText('Inscríbete como voluntario')).toBeInTheDocument()
    expect(screen.getByLabelText('Nombre completo')).toHaveValue('Laura Rescatista')

    await usuario.click(screen.getByRole('button', { name: 'Inscribirme' }))
    expect(screen.getByText('Elige al menos una habilidad.')).toBeInTheDocument()
    expect(inscribirVoluntario).not.toHaveBeenCalled()

    await usuario.type(screen.getByLabelText('Teléfono de contacto'), '3101234567')
    await usuario.click(screen.getByLabelText('Rescate'))
    await usuario.click(screen.getByRole('button', { name: 'Marcar en el mapa' }))
    await usuario.click(screen.getByRole('button', { name: 'Inscribirme' }))

    expect(inscribirVoluntario).toHaveBeenCalledWith({
      nombre: 'Laura Rescatista',
      telefono: '3101234567',
      habilidades: ['RESCATE'],
      ubicacion: [4.82, -75.67],
    })
    expect(await screen.findByText('Estás inscrito como voluntario')).toBeInTheDocument()
  })

  it('muestra el perfil y las asignaciones del voluntario', async () => {
    obtenerMiPerfil.mockResolvedValue(PERFIL)
    listarMisAsignaciones.mockResolvedValue([MISION])
    renderConApp(<Voluntariado />, { auth: { usuario: TECNICO } })

    expect(await screen.findByText('Estás inscrito como voluntario')).toBeInTheDocument()
    expect(screen.getByText('Primeros auxilios')).toBeInTheDocument()
    expect(await screen.findByText('Apoyar evacuación del sector')).toBeInTheDocument()
    expect(screen.getByText('Asignada')).toBeInTheDocument()
  })
})

describe('AsignarVoluntarios (CU-43)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('asigna una misión sobre un caso abierto', async () => {
    const usuario = userEvent.setup()
    listarVoluntarios.mockResolvedValue([PERFIL])
    listarCasos.mockResolvedValue([
      { id: 'c1', case_number: 'INC-1', incident_type: 'INUNDACION', status: 'REPORTADO' },
      { id: 'c2', case_number: 'INC-2', incident_type: 'OTRO', status: 'RESUELTO' },
    ])
    asignarVoluntario.mockResolvedValue(MISION)
    renderConApp(<AsignarVoluntarios />, { auth: { usuario: ADMIN } })

    expect(await screen.findByText('Laura Rescatista')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Asignar misión' }))

    const selector = await screen.findByLabelText('Caso')
    expect(screen.getByRole('option', { name: 'INC-1 · Inundación' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /INC-2/ })).not.toBeInTheDocument()
    expect(selector).toHaveValue('c1')

    await usuario.type(screen.getByLabelText('Tarea'), 'Apoyar evacuación del sector')
    await usuario.click(screen.getByRole('button', { name: 'Asignar' }))

    expect(asignarVoluntario).toHaveBeenCalledWith({
      voluntarioId: 'v1',
      casoId: 'c1',
      tarea: 'Apoyar evacuación del sector',
    })
    expect(await screen.findByText(/Misión asignada/)).toBeInTheDocument()
  })

  it('filtra por habilidad', async () => {
    const usuario = userEvent.setup()
    listarVoluntarios.mockResolvedValue([PERFIL])
    listarCasos.mockResolvedValue([])
    renderConApp(<AsignarVoluntarios />, { auth: { usuario: ADMIN } })

    await screen.findByText('Laura Rescatista')
    await usuario.selectOptions(screen.getByLabelText('Filtrar por habilidad'), 'CONDUCCION')
    expect(screen.getByText('No hay voluntarios disponibles')).toBeInTheDocument()
  })
})
