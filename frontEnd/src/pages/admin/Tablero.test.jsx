import { fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { descargarIncidentesCsv, obtenerIndicadoresBienestar, obtenerTablero } from '@/api/admin'
import { listarCasos, listarInspectores } from '@/api/casos'
import { renderConApp } from '@/test/utils'
import Tablero from './Tablero'

vi.mock('@/api/admin', async (original) => ({
  ...(await original()),
  obtenerTablero: vi.fn(),
  obtenerIndicadoresBienestar: vi.fn(),
  descargarIncidentesCsv: vi.fn(),
}))

vi.mock('@/api/casos', async (original) => ({
  ...(await original()),
  listarCasos: vi.fn(),
  listarInspectores: vi.fn(),
}))

const ADMIN = { id: 'a1', full_name: 'Ana Admin', role: 'administrador', neighborhood: 'Centro' }

const RESUMEN = {
  total_incidents: 12,
  incidents_by_status: { REPORTADO: 7, RESUELTO: 5 },
  incidents_by_severity: { ALTA: 4, CRITICA: 1 },
  total_inspections: 3,
  inspections_by_habitability: { EVACUACION: 2 },
  total_aid_needs: 9,
  total_aid_offers: 6,
  total_matches: 2,
  active_volunteers: 15,
}

function renderizar() {
  return renderConApp(<Tablero />, { auth: { usuario: ADMIN } })
}

describe('Tablero del Administrador (CU-45, CU-26, CU-46)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    obtenerTablero.mockResolvedValue(RESUMEN)
    obtenerIndicadoresBienestar.mockResolvedValue([])
    // 6 reportes en las últimas 24 h (λ = 0,25/h) y 2 inspectores (μ = 0,1/h).
    const haceUnaHora = new Date(Date.now() - 3_600_000).toISOString()
    listarCasos.mockResolvedValue(Array.from({ length: 6 }, () => ({ created_at: haceUnaHora })))
    listarInspectores.mockResolvedValue([{ id: 'i1' }, { id: 'i2' }])
  })

  it('muestra los totales y el desglose del tablero municipal (CU-45)', async () => {
    renderizar()

    const incidentes = (await screen.findByText('Incidentes reportados')).parentElement
    expect(within(incidentes).getByText('12')).toBeInTheDocument()
    expect(
      within(screen.getByText('Voluntarios disponibles').parentElement).getByText('15'),
    ).toBeInTheDocument()

    const porEstado = screen.getByRole('list', { name: 'Incidentes por estado' })
    expect(within(porEstado).getByText('Reportado')).toBeInTheDocument()
    expect(within(porEstado).getByText('7')).toBeInTheDocument()
    const porGravedad = screen.getByRole('list', { name: 'Incidentes por gravedad' })
    expect(within(porGravedad).getByText('Crítica')).toBeInTheDocument()
    expect(screen.getByText('Evacuación')).toBeInTheDocument()
  })

  it('muestra los indicadores de bienestar por barrio (CU-26)', async () => {
    obtenerIndicadoresBienestar.mockResolvedValue([
      { neighborhood: 'Cuba', sample_count: 4, average_mood: 3.25, crisis_alerts: 1 },
    ])
    renderizar()

    const barrio = (await screen.findByRole('heading', { name: 'Cuba' })).closest('li')
    expect(within(barrio).getByText(/4 respuestas/)).toBeInTheDocument()
    expect(within(barrio).getByText(/1 alerta de crisis/)).toBeInTheDocument()
    expect(within(barrio).getByText('Ánimo 3.3 / 5')).toBeInTheDocument()
  })

  it('avisa cuando ningún barrio alcanza el mínimo de respuestas', async () => {
    renderizar()
    expect(await screen.findByText('Aún no hay indicadores')).toBeInTheDocument()
  })

  it('muestra el error del backend si no se puede cargar el tablero', async () => {
    obtenerTablero.mockRejectedValue({
      response: { data: { error: { message: 'Solo administradores pueden consultar.' } } },
    })
    renderizar()
    expect(await screen.findByText('Solo administradores pueden consultar.')).toBeInTheDocument()
  })

  it('descarga el CSV de incidentes (CU-46)', async () => {
    const usuario = userEvent.setup()
    descargarIncidentesCsv.mockResolvedValue('prevenred_incidentes_20261116_1000.csv')
    renderizar()

    await usuario.click(screen.getByRole('button', { name: /Descargar CSV de incidentes/ }))

    expect(descargarIncidentesCsv).toHaveBeenCalled()
    expect(
      await screen.findByText('Descargado: prevenred_incidentes_20261116_1000.csv'),
    ).toBeInTheDocument()
  })

  it('proyecta los casos pendientes con la ecuación diferencial', async () => {
    const usuario = userEvent.setup()
    renderizar()

    const seccion = (
      await screen.findByRole('heading', { name: 'Proyección de casos pendientes' })
    ).closest('section')
    // B₀ = 12 incidentes − 5 resueltos = 7; equilibrio λ/μ = 0,5/0,1 = 5 (λ redondeado a 0,5).
    expect((await within(seccion).findByText('Pendientes hoy (B₀)')).nextSibling).toHaveTextContent(
      '7',
    )
    expect(within(seccion).getByText('Equilibrio λ/μ').nextSibling).toHaveTextContent('5')

    // Sin inspectores no hay equilibrio: los casos solo se acumulan.
    const inspectores = within(seccion).getByRole('slider', { name: /Inspectores atendiendo/ })
    fireEvent.change(inspectores, { target: { value: '0' } })
    expect(within(seccion).getByText('Equilibrio λ/μ').nextSibling).toHaveTextContent('Sin límite')
    await usuario.click(within(seccion).getByRole('button', { name: 'Volver a los datos reales' }))
    expect(within(seccion).getByText('Equilibrio λ/μ').nextSibling).toHaveTextContent('5')
  })
})
