import { api } from '@/api/client'
import {
  enlaceWhatsapp,
  filtrarTecnicos,
  guardarMiPerfil,
  listarTecnicos,
  obtenerMiPerfil,
  verificarTecnico,
  zonaCercana,
} from './oficiosya'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

const tecnico = (datos) => ({
  id: 't1',
  user_id: 'u1',
  full_name: 'Carlos Arango',
  phone_number: '+573101234567',
  specialties: ['PLOMERIA'],
  experience_years: 5,
  bio: 'Arreglo fugas',
  verification_status: 'VERIFICADO',
  rating_average: 4,
  reviews_count: 3,
  longitude: -75.731,
  latitude: 4.796,
  created_at: '2026-11-16T10:00:00Z',
  ...datos,
})

describe('API de OficiosYa', () => {
  beforeEach(() => vi.clearAllMocks())

  it('CU-19: busca cerca del barrio elegido y filtra por especialidad en el backend', async () => {
    api.get.mockResolvedValue({ data: [tecnico()] })
    const resultado = await listarTecnicos({ zona: 'Boston', especialidad: 'PLOMERIA' })

    expect(api.get).toHaveBeenCalledWith('/services/technicians/search', {
      params: {
        latitude: 4.809,
        longitude: -75.683,
        radius_meters: 3000,
        only_verified: true,
        specialty: 'PLOMERIA',
      },
    })
    expect(resultado[0]).toMatchObject({ coordenadas: [4.796, -75.731], zona: 'Cuba' })
  })

  it('CU-19: sin barrio busca en toda Pereira desde el centro', async () => {
    api.get.mockResolvedValue({ data: [] })
    await listarTecnicos({})
    expect(api.get.mock.calls[0][1].params).toMatchObject({
      latitude: 4.8133,
      longitude: -75.6961,
      radius_meters: 15000,
    })
  })

  it('filtra por texto (incluye el nombre del oficio) y valoración, y ordena por valoración', () => {
    const lista = [
      tecnico({ id: 'a', rating_average: 3.5 }),
      tecnico({ id: 'b', rating_average: 4.8, specialties: ['ELECTRICIDAD'], bio: '' }),
      tecnico({ id: 'c', rating_average: 4.6 }),
    ]
    expect(filtrarTecnicos(lista).map((t) => t.id)).toEqual(['b', 'c', 'a'])
    expect(filtrarTecnicos(lista, { valoracionMin: '4.5' }).map((t) => t.id)).toEqual(['b', 'c'])
    expect(filtrarTecnicos(lista, { texto: 'plomería' }).map((t) => t.id)).toEqual(['c', 'a'])
  })

  it('CU-22: el enlace de WhatsApp lo arma el backend', async () => {
    api.get.mockResolvedValue({ data: { whatsapp_url: 'https://wa.me/573101234567?text=Hola' } })
    expect(await enlaceWhatsapp(tecnico())).toBe('https://wa.me/573101234567?text=Hola')
    expect(api.get.mock.calls[0][0]).toBe('/services/technicians/t1/whatsapp')
    expect(api.get.mock.calls[0][1].params.message).toMatch(/^Hola Carlos/)
  })

  it('CU-17: sin perfil propio devuelve null; otros errores se propagan', async () => {
    api.get.mockRejectedValueOnce({ response: { status: 404 } })
    expect(await obtenerMiPerfil()).toBeNull()
    api.get.mockRejectedValueOnce({ response: { status: 500 } })
    await expect(obtenerMiPerfil()).rejects.toEqual({ response: { status: 500 } })
  })

  it('CU-17: guarda el perfil con los nombres de campo del backend', async () => {
    api.post.mockResolvedValue({ data: tecnico() })
    await guardarMiPerfil({
      nombre: ' Carlos Arango ',
      telefono: '310 123 4567',
      especialidades: ['PLOMERIA', 'PINTURA'],
      experiencia: '5',
      bio: ' Arreglo fugas ',
      coordenadas: [4.8, -75.7],
    })
    expect(api.post).toHaveBeenCalledWith('/services/technicians/profile', {
      full_name: 'Carlos Arango',
      phone_number: '310 123 4567',
      specialties: ['PLOMERIA', 'PINTURA'],
      experience_years: 5,
      bio: 'Arreglo fugas',
      latitude: 4.8,
      longitude: -75.7,
    })
  })

  it('CU-18: aprueba o rechaza con PATCH verify', async () => {
    api.patch.mockResolvedValue({ data: {} })
    await verificarTecnico('t1', false)
    expect(api.patch).toHaveBeenCalledWith('/services/technicians/t1/verify', { approve: false })
  })

  it('deriva el barrio más cercano a unas coordenadas', () => {
    expect(zonaCercana([4.8133, -75.6961])).toBe('Centro')
  })
})
