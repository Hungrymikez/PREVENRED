import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { reiniciarTema, TEMA_KEY } from '@/hooks/useTema'
import { LayoutAuth } from './LayoutAuth'

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route element={<LayoutAuth />}>
          <Route path="/login" element={<p>Formulario</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

const tema = () => screen.getByRole('main').dataset.tema

describe('LayoutAuth: tema claro y oscuro', () => {
  beforeEach(() => {
    localStorage.clear()
    reiniciarTema()
  })

  it('el interruptor cambia de tema, de foto y lo recuerda', async () => {
    renderLogin()
    const interruptor = screen.getByRole('switch', { name: 'Modo oscuro' })
    expect(tema()).toBe('claro')
    expect(interruptor).toHaveAttribute('aria-checked', 'false')
    expect(screen.getByText('Centro de Pereira, Risaralda')).toBeInTheDocument()

    await userEvent.click(interruptor)

    expect(tema()).toBe('oscuro')
    expect(interruptor).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByText(/Viaducto César Gaviria/)).toBeInTheDocument()
    expect(localStorage.getItem(TEMA_KEY)).toBe('oscuro')
  })

  it('abre con el tema que la persona eligió antes', () => {
    localStorage.setItem(TEMA_KEY, 'oscuro')
    reiniciarTema() // simula abrir la app de nuevo
    renderLogin()
    expect(tema()).toBe('oscuro')
  })
})
