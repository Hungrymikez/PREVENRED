import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import MenteResiliente from './MenteResiliente'

describe('Mente Resiliente', () => {
  beforeEach(() => localStorage.clear())

  it('pide consentimiento antes de mostrar la encuesta (CU-24)', async () => {
    renderConApp(<MenteResiliente />, { auth: { usuario: USUARIO_PRUEBA } })

    expect(screen.queryByText('¿Cómo te sientes esta semana?')).not.toBeInTheDocument()
    const continuar = screen.getByRole('button', { name: 'Continuar' })
    expect(continuar).toBeDisabled()

    await userEvent.click(screen.getByLabelText(/acepto participar/i))
    await userEvent.click(continuar)

    expect(await screen.findByText('¿Cómo te sientes esta semana?')).toBeInTheDocument()
  })

  it('exige elegir el ánimo y confirma el envío sin diagnóstico (CU-23)', async () => {
    localStorage.setItem('prevenred_consentimiento_bienestar', 'v1')
    renderConApp(<MenteResiliente />, { auth: { usuario: USUARIO_PRUEBA } })

    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }))
    expect(await screen.findByText('Elige cómo te sientes.')).toBeInTheDocument()

    await userEvent.click(screen.getByLabelText(/bien/i, { selector: 'input[value="4"]' }))
    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Gracias por contarnos cómo estás')).toBeInTheDocument()
  })

  it('siempre muestra a quién acudir (CU-27)', () => {
    renderConApp(<MenteResiliente />, { auth: { usuario: USUARIO_PRUEBA } })
    expect(screen.getByText('¿Necesitas hablar con alguien ahora?')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /123/ })).toHaveAttribute('href', 'tel:123')
  })
})
