import { screen } from '@testing-library/react'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import Panel from './Panel'

function abrir() {
  renderConApp(<Panel />, { auth: { usuario: USUARIO_PRUEBA }, ruta: '/panel' })
}

describe('Panel (menú principal)', () => {
  beforeEach(() => localStorage.clear())

  it('saluda, muestra el barrio y los módulos con su enlace', async () => {
    abrir()
    expect(screen.getByRole('heading', { name: 'Hola, Sara' })).toBeInTheDocument()
    expect(screen.getByText('Modo cotidiano')).toBeInTheDocument()

    for (const [nombre, ruta] of [
      ['SegundaVida', '/segundavida'],
      ['OficiosYa', '/oficiosya'],
      ['Mente Resiliente', '/mente-resiliente'],
      ['Mis casos', '/emergencia/casos'],
    ]) {
      expect(screen.getByRole('link', { name: new RegExp(nombre) })).toHaveAttribute('href', ruta)
    }
    // Fuera de la emergencia no se ofrece reportar: la ruta lo bloquearía (CU-29 E3).
    expect(screen.queryByText('¿Necesitas reportar algo?')).not.toBeInTheDocument()
  })

  it('en Modo Emergencia pone primero los reportes', async () => {
    localStorage.setItem('prevenred_modo_demo', JSON.stringify({ mode: 'EMERGENCIA' }))
    abrir()
    expect(await screen.findByText('¿Necesitas reportar algo?')).toBeInTheDocument()
    expect(screen.getByText('Modo Emergencia')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Otros servicios' })).toBeInTheDocument()
  })
})
