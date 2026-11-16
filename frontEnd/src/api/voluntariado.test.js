import { api } from '@/api/client'
import {
  asignarVoluntario,
  inscribirVoluntario,
  listarMisAsignaciones,
  listarVoluntarios,
  obtenerMiPerfil,
} from './voluntariado'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn() },
}))

describe('api de voluntariado (CU-38, CU-43, CU-44)', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
  })

  it('devuelve null cuando la persona aún no es voluntaria (404)', async () => {
    api.get.mockRejectedValue({ response: { status: 404 } })
    expect(await obtenerMiPerfil()).toBeNull()
  })

  it('propaga otros errores al consultar el perfil', async () => {
    api.get.mockRejectedValue({ response: { status: 500 } })
    await expect(obtenerMiPerfil()).rejects.toEqual({ response: { status: 500 } })
  })

  it('inscribe con habilidades y ubicación', async () => {
    api.post.mockResolvedValue({ data: { id: 'v1' } })
    await inscribirVoluntario({
      nombre: ' Laura ',
      telefono: '3101234567',
      habilidades: ['RESCATE'],
      ubicacion: [4.81, -75.69],
    })
    expect(api.post).toHaveBeenCalledWith('/volunteering/register', {
      full_name: 'Laura',
      phone_number: '3101234567',
      skills: ['RESCATE'],
      latitude: 4.81,
      longitude: -75.69,
    })
  })

  it('consulta asignaciones, voluntarios y asigna', async () => {
    api.get.mockResolvedValue({ data: [] })
    api.post.mockResolvedValue({ data: { id: 'a1' } })
    await listarMisAsignaciones()
    await listarVoluntarios()
    await asignarVoluntario({ voluntarioId: 'v1', casoId: 'c1', tarea: ' Evacuar familias ' })

    expect(api.get).toHaveBeenCalledWith('/volunteering/assignments/my')
    expect(api.get).toHaveBeenCalledWith('/volunteering/volunteers')
    expect(api.post).toHaveBeenCalledWith('/volunteering/assign', {
      volunteer_id: 'v1',
      incident_id: 'c1',
      task_description: 'Evacuar familias',
    })
  })
})
