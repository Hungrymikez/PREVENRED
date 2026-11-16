import { screen } from '@testing-library/react'
import { obtenerModo } from '@/api/modo'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import Panel from './Panel'

vi.mock('@/api/modo', () => ({ TIPOS_EVENTO: {}, obtenerModo: vi.fn(), cambiarModo: vi.fn() }))

const COTIDIANO = { mode: 'COTIDIANO', reason: '' }
const EMERGENCIA = { mode: 'EMERGENCIA', reason: 'Sismo en Pereira' }

function abrir(rol = 'ciudadano') {
  renderConApp(<Panel />, { auth: { usuario: { ...USUARIO_PRUEBA, role: rol } }, ruta: '/panel' })
}

describe('Panel (menú principal)', () => {
  beforeEach(() => {
    localStorage.clear()
    obtenerModo.mockResolvedValue(COTIDIANO)
  })

  it('el ciudadano ve sus servicios y Mis casos, pero no la bandeja ni el control del modo', async () => {
    abrir('ciudadano')
    expect(screen.getByRole('heading', { name: 'Hola, Sara' })).toBeInTheDocument()
    expect(await screen.findByText('Modo cotidiano')).toBeInTheDocument()

    for (const [nombre, ruta] of [
      ['SegundaVida', '/segundavida'],
      ['OficiosYa', '/oficiosya'],
      ['Mente Resiliente', '/mente-resiliente'],
      ['Mis casos', '/emergencia/casos'],
    ]) {
      expect(screen.getByRole('link', { name: new RegExp(nombre) })).toHaveAttribute('href', ruta)
    }
    expect(screen.queryByRole('link', { name: /^Casos/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Modo de la plataforma')).not.toBeInTheDocument()
  })

  it('el inspector ve la bandeja de casos y no Mis casos ni el control del modo', async () => {
    abrir('inspector')
    expect(await screen.findByRole('link', { name: /^Casos/ })).toHaveAttribute('href', '/casos')
    expect(screen.queryByRole('link', { name: /Mis casos/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Modo de la plataforma')).not.toBeInTheDocument()
  })

  it('solo el administrador ve el control del modo (CU-04, RN-01)', async () => {
    abrir('administrador')
    expect(await screen.findByText('Modo de la plataforma')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Activar Modo Emergencia' })).toBeInTheDocument()
  })

  it('en Modo Emergencia el ciudadano ve primero los reportes', async () => {
    obtenerModo.mockResolvedValue(EMERGENCIA)
    abrir('ciudadano')
    expect(await screen.findByText('¿Necesitas reportar algo?')).toBeInTheDocument()
    expect(screen.getByText('Modo Emergencia')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Otros servicios' })).toBeInTheDocument()
  })

  it('en Modo Emergencia el inspector va a atender casos, no a reportar', async () => {
    obtenerModo.mockResolvedValue(EMERGENCIA)
    abrir('inspector')
    expect(await screen.findByRole('link', { name: /Atender casos reportados/ })).toHaveAttribute(
      'href',
      '/casos',
    )
    expect(screen.queryByText('¿Necesitas reportar algo?')).not.toBeInTheDocument()
  })
})
