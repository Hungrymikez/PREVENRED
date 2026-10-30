import { PUBLICACIONES } from '@/api/mocks/datos'
import { filtrarPublicaciones } from './segundavida'

describe('filtrarPublicaciones (CU-12)', () => {
  it('filtra por modalidad', () => {
    const resultado = filtrarPublicaciones(PUBLICACIONES, { modalidad: 'ALQUILER' })
    expect(resultado.length).toBeGreaterThan(0)
    expect(resultado.every((p) => p.offerType === 'ALQUILER')).toBe(true)
  })

  it('filtra por categoría, estado y precio máximo', () => {
    const resultado = filtrarPublicaciones(PUBLICACIONES, {
      categoria: 'Construcción',
      condicion: 'buen_estado',
      precioMax: '100000',
    })
    expect(resultado.map((p) => p.id)).toEqual(['m1'])
  })

  it('busca en título y descripción sin importar mayúsculas', () => {
    expect(filtrarPublicaciones(PUBLICACIONES, { texto: 'TALADRO' }).map((p) => p.id)).toEqual([
      'h1',
    ])
  })

  it('ordena de la más cercana a la más lejana', () => {
    const distancias = filtrarPublicaciones(PUBLICACIONES).map((p) => p.distanciaKm)
    expect(distancias).toEqual([...distancias].sort((a, b) => a - b))
  })
})
