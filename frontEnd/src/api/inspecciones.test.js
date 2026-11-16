import { api } from '@/api/client'
import { listarInspecciones, registrarInspeccion } from './inspecciones'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn() },
}))

describe('api de inspecciones (CU-34, CU-35, CU-36)', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
  })

  it('lista las inspecciones del backend', async () => {
    api.get.mockResolvedValue({ data: [{ id: 'i1' }] })
    expect(await listarInspecciones()).toEqual([{ id: 'i1' }])
    expect(api.get).toHaveBeenCalledWith('/fieldwork/inspections', { params: { limit: 100 } })
  })

  it('envía la inspección con los nombres del backend y la referencia al caso', async () => {
    api.post.mockResolvedValue({ data: { id: 'i1' } })
    await registrarInspeccion({
      direccion: ' Calle 14 # 9-30 ',
      barrio: 'Cuba',
      residentes: '3',
      nivelDano: 'SEVERO',
      habitabilidad: 'EVACUACION',
      notas: 'Grietas en muro de carga',
      ubicacion: [4.81, -75.69],
      caso: 'INC-1',
    })
    expect(api.post).toHaveBeenCalledWith('/fieldwork/inspections', {
      property_address: 'Calle 14 # 9-30',
      neighborhood: 'Cuba',
      residents_count: 3,
      damage_level: 'SEVERO',
      habitability: 'EVACUACION',
      technical_notes: '[Caso INC-1] Grietas en muro de carga',
      latitude: 4.81,
      longitude: -75.69,
      photos: [],
    })
  })
})
