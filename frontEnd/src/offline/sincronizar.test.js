import { crearReporte } from '@/api/incidentes'
import { eliminarPendiente, guardarPendiente, listarPendientes } from './almacen'
import { sincronizarPendientes } from './sincronizar'

vi.mock('@/api/incidentes', () => ({ crearReporte: vi.fn() }))

const reporte = (type) => ({ categoria: 'via', type, coordenadas: [4.8, -75.7] })
const errorDelServidor = (status, message) => ({
  response: { status, data: { error: { message } } },
})

describe('sincronizarPendientes (CU-37)', () => {
  // Con llaves: si la flecha devolviera el mock, Vitest lo ejecutaría como limpieza al final.
  beforeEach(() => {
    crearReporte.mockReset()
  })
  afterEach(async () => {
    for (const p of await listarPendientes()) await eliminarPendiente(p.clientId)
  })

  it('envía en orden, con su clientId, y borra la copia local', async () => {
    const a = await guardarPendiente(reporte('VIA_BLOQUEADA'))
    const b = await guardarPendiente(reporte('ARBOL_CAIDO'))
    crearReporte.mockResolvedValue({ caseId: 'PR-2026-00100' })

    expect(await sincronizarPendientes()).toBe(2)

    expect(crearReporte.mock.calls.map(([d]) => d.clientId)).toEqual([a.clientId, b.clientId])
    expect(crearReporte.mock.calls[0][0].reportedAt).toBe(a.creadoEn) // conserva la hora real
    expect(await listarPendientes()).toEqual([])
  })

  it('sin red se detiene y conserva todo para después (A2)', async () => {
    await guardarPendiente(reporte('VIA_BLOQUEADA'))
    await guardarPendiente(reporte('ARBOL_CAIDO'))
    crearReporte.mockRejectedValue(new Error('Network Error'))

    expect(await sincronizarPendientes()).toBe(0)
    expect(crearReporte).toHaveBeenCalledTimes(1)
    expect(await listarPendientes()).toHaveLength(2)
  })

  it('si el servidor rechaza uno, lo marca y sigue con los demás (E1)', async () => {
    await guardarPendiente(reporte('VIA_BLOQUEADA'))
    await guardarPendiente(reporte('ARBOL_CAIDO'))
    crearReporte
      .mockRejectedValueOnce(errorDelServidor(422, 'Ubicación fuera de Pereira.'))
      .mockResolvedValueOnce({ caseId: 'PR-2026-00101' })

    expect(await sincronizarPendientes()).toBe(1)
    const restantes = await listarPendientes()
    expect(restantes).toHaveLength(1)
    expect(restantes[0]).toMatchObject({ estado: 'error', error: 'Ubicación fuera de Pereira.' })
  })

  it('con la sesión vencida conserva la cola (E3)', async () => {
    await guardarPendiente(reporte('VIA_BLOQUEADA'))
    crearReporte.mockRejectedValue(errorDelServidor(401, 'Sesión vencida'))

    await sincronizarPendientes()
    expect((await listarPendientes())[0].estado).toBe('pendiente')
  })

  it('no envía dos veces si se llama mientras ya está sincronizando', async () => {
    await guardarPendiente(reporte('VIA_BLOQUEADA'))
    crearReporte.mockResolvedValue({ caseId: 'PR-2026-00102' })

    await Promise.all([sincronizarPendientes(), sincronizarPendientes()])
    expect(crearReporte).toHaveBeenCalledTimes(1)
  })
})
