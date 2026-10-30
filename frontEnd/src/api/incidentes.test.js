import { crearReporte, nombreEstado, obtenerCaso } from './incidentes'

describe('incidentes (CU-29 a CU-32)', () => {
  it('crea el caso en estado Reportado con un número único', async () => {
    const datos = { categoria: 'via', type: 'ARBOL_CAIDO', coordenadas: [4.8, -75.7] }
    const a = await crearReporte(datos)
    const b = await crearReporte(datos)

    expect(a.status).toBe('REPORTADO')
    expect(a.caseId).toMatch(/^PR-2026-\d{5}$/)
    expect(a.caseId).not.toBe(b.caseId)
  })

  it('encuentra un caso propio aunque se escriba en minúsculas', async () => {
    const caso = await obtenerCaso(' pr-2026-00041 ')
    expect(caso.type).toBe('DESLIZAMIENTO')
  })

  it('no revela si un caso ajeno existe (E1)', async () => {
    await expect(obtenerCaso('PR-2026-99999')).rejects.toThrow(/no encontramos/i)
  })

  it('las vías se cierran como "Despejado"', () => {
    expect(nombreEstado('RESUELTO', 'via')).toBe('Despejado')
    expect(nombreEstado('RESUELTO', 'vivienda')).toBe('Resuelto')
  })
})
