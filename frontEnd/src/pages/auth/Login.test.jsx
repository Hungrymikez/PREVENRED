import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderConApp } from '@/test/utils'
import Login from './Login'

describe('Login', () => {
  it('valida los campos vacíos sin llamar al backend', async () => {
    const iniciarSesion = vi.fn()
    renderConApp(<Login />, { auth: { iniciarSesion } })

    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('Escribe tu correo.')).toBeInTheDocument()
    expect(screen.getByText('Escribe tu contraseña.')).toBeInTheDocument()
    expect(iniciarSesion).not.toHaveBeenCalled()
  })

  it('envía el correo y la contraseña', async () => {
    const iniciarSesion = vi.fn().mockResolvedValue({})
    renderConApp(<Login />, { auth: { iniciarSesion } })

    await userEvent.type(screen.getByLabelText('Correo electrónico'), 'sara@correo.com')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'clave-segura')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(iniciarSesion).toHaveBeenCalledWith('sara@correo.com', 'clave-segura')
  })

  it('muestra el error que devuelve el backend', async () => {
    const iniciarSesion = vi.fn().mockRejectedValue({
      response: { data: { error: { message: 'Correo o contraseña incorrectos.' } } },
    })
    renderConApp(<Login />, { auth: { iniciarSesion } })

    await userEvent.type(screen.getByLabelText('Correo electrónico'), 'sara@correo.com')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'mala-clave')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.')
  })
})
