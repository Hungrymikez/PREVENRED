import { api } from '@/api/client'
import {
  ejecutarEmparejamiento,
  formatearCantidad,
  listarMisOfertas,
  listarNecesidadesPendientes,
  listarOfertasPendientes,
  ofrecerAyuda,
} from './donaciones'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn() },
}))

describe('api de donaciones (CU-33, CU-41, CU-42)', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
  })

  it('ofrece ayuda con los nombres del backend', async () => {
    api.post.mockResolvedValue({ data: { id: 'o1' } })
    await ofrecerAyuda({
      titulo: ' Agua embotellada ',
      categoria: 'AGUA',
      cantidad: '20',
      unidad: 'litros',
      ubicacion: [4.81, -75.69],
    })
    expect(api.post).toHaveBeenCalledWith('/aid/offers', {
      title: 'Agua embotellada',
      category: 'AGUA',
      quantity: 20,
      unit: 'litros',
      latitude: 4.81,
      longitude: -75.69,
    })
  })

  it('consulta las listas y ejecuta el emparejamiento', async () => {
    api.get.mockResolvedValue({ data: [] })
    api.post.mockResolvedValue({ data: [{ id: 'm1' }] })
    await listarMisOfertas()
    await listarNecesidadesPendientes()
    await listarOfertasPendientes()
    expect(await ejecutarEmparejamiento()).toEqual([{ id: 'm1' }])

    expect(api.get).toHaveBeenCalledWith('/aid/offers/mine')
    expect(api.get).toHaveBeenCalledWith('/aid/needs/pending')
    expect(api.get).toHaveBeenCalledWith('/aid/offers/pending')
    expect(api.post).toHaveBeenCalledWith('/aid/matching/run')
  })

  it('formatea cantidades con su unidad', () => {
    expect(formatearCantidad(12.5, 'kg')).toBe('12,5 kg')
    expect(formatearCantidad(3, 'litros')).toBe('3 litros')
  })
})
