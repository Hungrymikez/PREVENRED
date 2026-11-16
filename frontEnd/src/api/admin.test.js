import { api } from '@/api/client'
import {
  descargarIncidentesCsv,
  listarAuditoria,
  obtenerIndicadoresBienestar,
  obtenerTablero,
} from './admin'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn() },
}))

describe('api/admin', () => {
  beforeEach(() => {
    api.get.mockReset()
  })

  it('consulta el tablero municipal y los indicadores de bienestar (CU-45, CU-26)', async () => {
    api.get.mockResolvedValue({ data: {} })
    await obtenerTablero()
    await obtenerIndicadoresBienestar()
    expect(api.get).toHaveBeenNthCalledWith(1, '/reporting/dashboard')
    expect(api.get).toHaveBeenNthCalledWith(2, '/wellbeing/indicators')
  })

  it('descarga el CSV de incidentes como archivo (CU-46)', async () => {
    api.get.mockResolvedValue({
      data: { filename: 'prevenred_incidentes_20261116_1000.csv', csv_content: 'a,b\n1,2\n' },
    })
    const crear = vi.fn(() => 'blob:csv')
    const revocar = vi.fn()
    vi.stubGlobal('URL', { ...URL, createObjectURL: crear, revokeObjectURL: revocar })
    const clic = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    const nombre = await descargarIncidentesCsv()

    expect(api.get).toHaveBeenCalledWith('/reporting/export/incidents/csv')
    expect(nombre).toBe('prevenred_incidentes_20261116_1000.csv')
    expect(crear.mock.calls[0][0]).toBeInstanceOf(Blob)
    expect(clic).toHaveBeenCalled()
    expect(revocar).toHaveBeenCalledWith('blob:csv')

    clic.mockRestore()
    vi.unstubAllGlobals()
  })

  it('lista la auditoría con filtro de recurso y límite (CU-09)', async () => {
    api.get.mockResolvedValue({ data: [] })
    await listarAuditoria()
    expect(api.get).toHaveBeenLastCalledWith('/audit/logs', { params: { limit: 50 } })

    await listarAuditoria({ recurso: 'incidents', limite: 100 })
    expect(api.get).toHaveBeenLastCalledWith('/audit/logs', {
      params: { limit: 100, resource: 'incidents' },
    })
  })
})
