import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  enviarRegistro,
  obtenerLineasDeAyuda,
  obtenerMiConsentimiento,
  otorgarConsentimiento,
} from '@/api/bienestar'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import MenteResiliente from './MenteResiliente'

vi.mock('@/api/bienestar', async (original) => ({
  ...(await original()),
  obtenerMiConsentimiento: vi.fn(),
  otorgarConsentimiento: vi.fn(),
  enviarRegistro: vi.fn(),
  obtenerLineasDeAyuda: vi.fn(),
}))

const CONSENTIMIENTO = {
  user_id: 'u1',
  terms_version: 'v1.0',
  consented_at: '2026-11-16T10:00:00Z',
  is_revoked: false,
}

const LINEAS = {
  city: 'Pereira, Risaralda',
  helplines: [
    { name: 'Línea de la Esperanza / Salud Mental', phone: '106', type: 'Gratuita 24/7' },
    { name: 'Emergencias Generales', phone: '123', type: 'Policía / Cruz Roja / Bomberos' },
  ],
}

function renderizar() {
  return renderConApp(<MenteResiliente />, { auth: { usuario: USUARIO_PRUEBA } })
}

describe('Mente Resiliente', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    obtenerLineasDeAyuda.mockResolvedValue(LINEAS)
  })

  it('pide consentimiento y lo registra en el backend antes de mostrar la encuesta (CU-24)', async () => {
    const usuario = userEvent.setup()
    obtenerMiConsentimiento.mockResolvedValue(null)
    otorgarConsentimiento.mockResolvedValue(CONSENTIMIENTO)
    renderizar()

    const continuar = await screen.findByRole('button', { name: 'Continuar' })
    expect(screen.queryByText('¿Cómo te sientes esta semana?')).not.toBeInTheDocument()
    expect(continuar).toBeDisabled()

    await usuario.click(screen.getByLabelText(/acepto participar/i))
    await usuario.click(continuar)

    expect(otorgarConsentimiento).toHaveBeenCalled()
    expect(await screen.findByText('¿Cómo te sientes esta semana?')).toBeInTheDocument()
  })

  it('exige el ánimo y envía la encuesta con el barrio de la cuenta (CU-23)', async () => {
    const usuario = userEvent.setup()
    obtenerMiConsentimiento.mockResolvedValue(CONSENTIMIENTO)
    enviarRegistro.mockResolvedValue({ crisis_detected: false, crisis_support_message: null })
    renderizar()

    const enviar = await screen.findByRole('button', { name: 'Enviar' })
    expect(screen.getByLabelText('Barrio o comuna')).toHaveValue('Cuba')

    await usuario.click(enviar)
    expect(await screen.findByText('Elige cómo te sientes.')).toBeInTheDocument()
    expect(enviarRegistro).not.toHaveBeenCalled()

    await usuario.click(screen.getByLabelText(/bien/i, { selector: 'input[value="4"]' }))
    await usuario.type(screen.getByLabelText(/contarnos algo más/i), '  Tranquilo  ')
    await usuario.click(enviar)

    expect(await screen.findByText('Gracias por contarnos cómo estás')).toBeInTheDocument()
    expect(enviarRegistro.mock.calls[0][0]).toEqual({
      animo: 4,
      texto: 'Tranquilo',
      barrio: 'Cuba',
    })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('muestra el mensaje de canalización del backend cuando detecta crisis (RF-18)', async () => {
    const usuario = userEvent.setup()
    obtenerMiConsentimiento.mockResolvedValue(CONSENTIMIENTO)
    enviarRegistro.mockResolvedValue({
      crisis_detected: true,
      crisis_support_message: 'No estás solo/a: marca al 106.',
    })
    renderizar()

    await usuario.click(await screen.findByLabelText(/muy mal/i, { selector: 'input[value="1"]' }))
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No estás solo/a: marca al 106.')
  })

  it('muestra las líneas de ayuda del backend, haya o no consentimiento (CU-27)', async () => {
    obtenerMiConsentimiento.mockResolvedValue(null)
    renderizar()

    expect(screen.getByText('¿Necesitas hablar con alguien ahora?')).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /106/ })).toHaveAttribute('href', 'tel:106')
    expect(screen.getByRole('link', { name: /123/ })).toHaveAttribute('href', 'tel:123')
  })

  it('si no cargan las líneas, deja al menos la de emergencias (CU-27)', async () => {
    obtenerMiConsentimiento.mockResolvedValue(null)
    obtenerLineasDeAyuda.mockRejectedValue(new Error('sin red'))
    renderizar()

    expect(await screen.findByRole('link', { name: /123/ })).toHaveAttribute('href', 'tel:123')
  })
})
