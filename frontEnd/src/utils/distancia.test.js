import { distanciaKm, formatearDistancia, formatearPesos } from './distancia'

describe('distanciaKm', () => {
  it('es cero entre el mismo punto', () => {
    expect(distanciaKm([4.81, -75.69], [4.81, -75.69])).toBe(0)
  })

  it('calcula distancias cortas dentro de Pereira', () => {
    // Centro -> Cuba: unos 4 km en línea recta.
    const km = distanciaKm([4.8133, -75.6961], [4.796, -75.731])
    expect(km).toBeGreaterThan(3.5)
    expect(km).toBeLessThan(4.8)
  })
})

describe('formatos', () => {
  it('muestra metros, kilómetros o "menos de 100 m"', () => {
    expect(formatearDistancia(0.05)).toBe('a menos de 100 m')
    expect(formatearDistancia(0.42)).toBe('a 420 m')
    expect(formatearDistancia(2.345)).toBe('a 2,3 km')
  })

  it('muestra pesos colombianos sin decimales', () => {
    expect(formatearPesos(25000)).toMatch(/\$\s?25\.000/)
  })
})
