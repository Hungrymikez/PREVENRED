import { TECNICOS } from '@/api/mocks/datos'
import { filtrarTecnicos } from './oficiosya'

describe('filtrarTecnicos (CU-19)', () => {
  it('solo muestra técnicos verificados', () => {
    const resultado = filtrarTecnicos(TECNICOS)
    expect(resultado.every((t) => t.verificationStatus === 'VERIFICADO')).toBe(true)
    expect(resultado.find((t) => t.id === 't5')).toBeUndefined() // t5 está PENDIENTE
  })

  it('filtra por especialidad y zona', () => {
    const resultado = filtrarTecnicos(TECNICOS, { especialidad: 'Electricidad', zona: 'Centro' })
    expect(resultado.map((t) => t.id)).toEqual(['t2'])
  })

  it('filtra por valoración mínima y disponibilidad', () => {
    const resultado = filtrarTecnicos(TECNICOS, { valoracionMin: '4.5', soloDisponibles: 'si' })
    expect(resultado.every((t) => t.rating >= 4.5 && t.disponible)).toBe(true)
    expect(resultado.find((t) => t.id === 't3')).toBeUndefined() // 4,9 pero ocupado
  })

  it('ordena por mejor valoración', () => {
    const notas = filtrarTecnicos(TECNICOS).map((t) => t.rating)
    expect(notas).toEqual([...notas].sort((a, b) => b - a))
  })
})
