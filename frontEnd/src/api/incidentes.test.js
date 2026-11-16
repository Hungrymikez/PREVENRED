import { api } from '@/api/client'
import { subirArchivo } from '@/api/media'
import { crearReporte, listarMisCasos, nombreEstado, obtenerCaso } from './incidentes'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn() },
}))
vi.mock('@/api/media', () => ({ subirArchivo: vi.fn() }))

const INCIDENTE = {
  id: '6650aa',
  case_number: 'INC-20261116-ABC123',
  incident_type: 'VIVIENDA_DANADA',
  severity: 'MEDIA',
  status: 'EN_REVISION',
  description: 'Grietas en muros: la pared se partió',
  longitude: -75.69,
  latitude: 4.81,
  reported_by: 'u1',
  media_urls: [],
  created_at: '2026-11-16T10:00:05Z',
  reported_at: '2026-11-16T10:00:00Z',
  history: [
    {
      from_status: 'REPORTADO',
      to_status: 'EN_REVISION',
      changed_at: '2026-11-16T11:00:00Z',
      notes: 'Revisando',
    },
  ],
}

const AYUDA = {
  id: '6650bb00000000000000ff12',
  title: 'Agua',
  category: 'AGUA',
  quantity: 4,
  unit: 'personas',
  priority: 'ALTA',
  requester_id: 'u1',
  longitude: -75.7,
  latitude: 4.8,
  status: 'EMPAREJADO',
  created_at: '2026-11-16T09:00:00Z',
}

describe('incidentes conectados al backend (CU-29 a CU-32)', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
    subirArchivo.mockReset()
  })

  it('envía el daño en vivienda con el tipo, la descripción y el clientId que espera el backend', async () => {
    api.post.mockResolvedValue({ data: { ...INCIDENTE, status: 'REPORTADO', history: [] } })
    const caso = await crearReporte({
      categoria: 'vivienda',
      type: 'GRIETAS',
      description: ' la pared se partió ',
      coordenadas: [4.81, -75.69],
      clientId: 'cel-1',
      reportedAt: '2026-11-16T10:00:00Z',
    })

    expect(api.post).toHaveBeenCalledWith('/incidents/', {
      incident_type: 'VIVIENDA_DANADA',
      severity: 'MEDIA',
      description: 'Grietas en muros: la pared se partió',
      longitude: -75.69,
      latitude: 4.81,
      media_urls: [],
      client_id: 'cel-1',
      reported_at: '2026-11-16T10:00:00Z',
    })
    expect(caso).toMatchObject({
      caseId: 'INC-20261116-ABC123',
      categoria: 'vivienda',
      status: 'REPORTADO',
      coordenadas: [4.81, -75.69],
    })
  })

  it('sube la foto del daño (CU-47) y la envía en media_urls, también si venía guardada sin conexión', async () => {
    subirArchivo.mockResolvedValue('/static/uploads/abc.jpg')
    api.post.mockResolvedValue({ data: INCIDENTE })
    const foto = new Blob(['bytes'], { type: 'image/jpeg' })
    await crearReporte({
      categoria: 'via',
      type: 'VIA_BLOQUEADA',
      coordenadas: [4.81, -75.69],
      foto,
      clientId: 'cel-2',
    })

    expect(subirArchivo).toHaveBeenCalledWith(foto)
    expect(api.post).toHaveBeenCalledWith(
      '/incidents/',
      expect.objectContaining({ media_urls: ['/static/uploads/abc.jpg'], client_id: 'cel-2' }),
    )
  })

  it('si la foto no se puede subir por falta de red, no envía el reporte (queda para después)', async () => {
    subirArchivo.mockRejectedValue(new Error('Network Error'))
    await expect(
      crearReporte({
        categoria: 'vivienda',
        type: 'GRIETAS',
        coordenadas: [4.81, -75.69],
        foto: new Blob(['x'], { type: 'image/jpeg' }),
      }),
    ).rejects.toThrow('Network Error')
    expect(api.post).not.toHaveBeenCalled()
  })

  it('pide ayuda en aid_needs con la categoría y el número de personas', async () => {
    api.post.mockResolvedValue({ data: { ...AYUDA, status: 'PENDIENTE' } })
    const caso = await crearReporte({
      categoria: 'ayuda',
      type: 'AGUA',
      quantity: '4',
      coordenadas: [4.8, -75.7],
      foto: new Blob(['x'], { type: 'image/jpeg' }),
    })
    expect(subirArchivo).not.toHaveBeenCalled() // la ayuda no lleva foto

    expect(api.post).toHaveBeenCalledWith('/aid/needs', {
      title: 'Agua',
      category: 'AGUA',
      quantity: 4,
      unit: 'personas',
      priority: 'ALTA',
      longitude: -75.7,
      latitude: 4.8,
    })
    expect(caso).toMatchObject({ caseId: 'AY-00FF12', categoria: 'ayuda', status: 'REPORTADO' })
  })

  it('Mis casos junta reportes y solicitudes de ayuda, más recientes primero', async () => {
    api.get.mockImplementation((url) =>
      Promise.resolve({ data: url === '/aid/needs/mine' ? [AYUDA] : [INCIDENTE] }),
    )
    const casos = await listarMisCasos()
    expect(casos.map((c) => c.caseId)).toEqual(['INC-20261116-ABC123', 'AY-00FF12'])
    expect(casos[1].status).toBe('ASIGNADO') // EMPAREJADO en aid_needs
  })

  it('el detalle trae el historial de estados del backend', async () => {
    api.get.mockResolvedValue({ data: INCIDENTE })
    const caso = await obtenerCaso(' inc-20261116-abc123 ')

    expect(api.get).toHaveBeenCalledWith('/incidents/case/INC-20261116-ABC123')
    expect(caso.historial.map((h) => h.toStatus)).toEqual(['REPORTADO', 'EN_REVISION'])
    expect(caso.historial[1].note).toBe('Revisando')
  })

  it('no revela si un caso ajeno existe (E1)', async () => {
    api.get.mockRejectedValue({ response: { status: 404, data: {} } })
    await expect(obtenerCaso('INC-20261116-ZZZZZZ')).rejects.toThrow(/no encontramos/i)
  })

  it('las vías se cierran como "Despejado"', () => {
    expect(nombreEstado('RESUELTO', 'via')).toBe('Despejado')
    expect(nombreEstado('RESUELTO', 'vivienda')).toBe('Resuelto')
  })
})
