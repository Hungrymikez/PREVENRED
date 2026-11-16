import { api } from '@/api/client'
import { subirArchivo } from '@/api/media'
import { coordenadasDeZona } from '@/utils/zonas'
import {
  barrioCercano,
  filtrarPublicaciones,
  listarPublicaciones,
  obtenerPublicacion,
  publicar,
} from './segundavida'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn() },
}))
vi.mock('@/api/media', async (original) => ({
  ...(await original()),
  subirArchivo: vi.fn(),
}))

const [LAT_CUBA, LNG_CUBA] = coordenadasDeZona('Cuba')

/** Material tal como lo responde el backend. */
const material = (extra = {}) => ({
  id: 'm1',
  title: 'Tejas de zinc',
  description: 'Seis tejas en buen estado',
  category: 'CONSTRUCCION',
  offer_type: 'VENTA',
  condition: 'BUENO',
  quantity: 6,
  unit: 'unidades',
  price: 30000,
  longitude: LNG_CUBA,
  latitude: LAT_CUBA,
  owner_id: 'u1',
  owner_name: 'Sara S.',
  media_urls: ['/static/uploads/a.jpg'],
  is_active: true,
  created_at: '2026-11-16T10:00:00Z',
  ...extra,
})

describe('SegundaVida conectada al backend (CU-11, CU-12)', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
    subirArchivo.mockReset()
  })

  it('busca cerca del barrio elegido con la modalidad y la categoría del backend', async () => {
    api.get.mockResolvedValue({ data: [material()] })
    const [p] = await listarPublicaciones({
      modalidad: 'VENTA',
      categoria: 'CONSTRUCCION',
      cerca: 'Cuba',
    })

    expect(api.get).toHaveBeenCalledWith('/marketplace/materials/search', {
      params: expect.objectContaining({
        latitude: LAT_CUBA,
        longitude: LNG_CUBA,
        offer_type: 'VENTA',
        category: 'CONSTRUCCION',
      }),
    })
    expect(p).toMatchObject({
      id: 'm1',
      offerType: 'VENTA',
      condition: 'BUENO',
      zona: 'Cuba',
      distanciaKm: 0,
      ownerName: 'Sara S.',
      mediaUrls: ['/static/uploads/a.jpg'],
      coordenadas: [LAT_CUBA, LNG_CUBA],
    })
  })

  it('sin barrio busca desde el centro de Pereira', async () => {
    api.get.mockResolvedValue({ data: [] })
    await listarPublicaciones({})
    expect(api.get.mock.calls[0][1].params).toMatchObject({ latitude: 4.8133, longitude: -75.6961 })
  })

  it('el detalle inexistente da un mensaje claro', async () => {
    api.get.mockRejectedValue({ response: { status: 404, data: {} } })
    await expect(obtenerPublicacion('nada')).rejects.toThrow('La publicación no existe.')
  })

  it('publica subiendo cada foto primero y enviando sus URLs en media_urls', async () => {
    subirArchivo.mockResolvedValueOnce('/static/uploads/1.jpg')
    subirArchivo.mockResolvedValueOnce('/static/uploads/2.jpg')
    api.post.mockResolvedValue({ data: material({ media_urls: ['/static/uploads/1.jpg'] }) })

    const fotos = [new File(['a'], 'a.jpg', { type: 'image/jpeg' }), new File(['b'], 'b.jpg')]
    await publicar(
      {
        offerType: 'DONACION',
        title: ' Tejas ',
        description: 'Tejas de zinc',
        category: 'CONSTRUCCION',
        condition: 'USADO',
        quantity: '2',
        unit: 'unidades',
        price: '',
        zona: 'Cuba',
      },
      fotos,
    )

    expect(subirArchivo).toHaveBeenCalledTimes(2)
    expect(api.post).toHaveBeenCalledWith('/marketplace/materials', {
      title: 'Tejas',
      description: 'Tejas de zinc',
      category: 'CONSTRUCCION',
      offer_type: 'DONACION',
      condition: 'USADO',
      quantity: 2,
      unit: 'unidades',
      price: null,
      longitude: LNG_CUBA,
      latitude: LAT_CUBA,
      media_urls: ['/static/uploads/1.jpg', '/static/uploads/2.jpg'],
    })
  })

  it('muestra el mensaje del backend si rechaza la publicación', async () => {
    api.post.mockRejectedValue({
      response: { data: { error: { message: 'Para venta o alquiler se requiere un precio.' } } },
    })
    await expect(
      publicar({ offerType: 'VENTA', title: 'x', description: '', zona: 'Cuba' }),
    ).rejects.toThrow('Para venta o alquiler se requiere un precio.')
  })
})

describe('filtrarPublicaciones (CU-12)', () => {
  const lista = [
    {
      id: 'a',
      title: 'Taladro',
      description: '',
      condition: 'NUEVO',
      price: 50000,
      distanciaKm: 3,
    },
    {
      id: 'b',
      title: 'Tejas',
      description: 'zinc',
      condition: 'USADO',
      price: 1000,
      distanciaKm: 1,
    },
  ]

  it('filtra por estado, precio máximo y texto sin importar mayúsculas', () => {
    expect(filtrarPublicaciones(lista, { condicion: 'USADO' }).map((p) => p.id)).toEqual(['b'])
    expect(filtrarPublicaciones(lista, { precioMax: '2000' }).map((p) => p.id)).toEqual(['b'])
    expect(filtrarPublicaciones(lista, { texto: 'TALADRO' }).map((p) => p.id)).toEqual(['a'])
  })

  it('ordena de la más cercana a la más lejana', () => {
    expect(filtrarPublicaciones(lista).map((p) => p.id)).toEqual(['b', 'a'])
  })
})

describe('barrioCercano', () => {
  it('muestra el barrio más cercano o "Pereira" si está lejos de todos', () => {
    expect(barrioCercano([4.7965, -75.7305])).toBe('Cuba')
    expect(barrioCercano([5.2, -75.2])).toBe('Pereira')
  })
})
