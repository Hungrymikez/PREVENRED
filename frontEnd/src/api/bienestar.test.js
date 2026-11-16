import { api } from '@/api/client'
import {
  enviarRegistro,
  obtenerLineasDeAyuda,
  obtenerMiConsentimiento,
  otorgarConsentimiento,
} from './bienestar'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { get: vi.fn(), post: vi.fn() },
}))

describe('api/bienestar (Mente Resiliente)', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
  })

  it('consulta el consentimiento propio y devuelve null si no existe (CU-24)', async () => {
    api.get.mockResolvedValueOnce({ data: { terms_version: 'v1.0', is_revoked: false } })
    expect(await obtenerMiConsentimiento()).toEqual({ terms_version: 'v1.0', is_revoked: false })
    expect(api.get).toHaveBeenCalledWith('/wellbeing/consent/me')

    api.get.mockRejectedValueOnce({ response: { status: 404 } })
    expect(await obtenerMiConsentimiento()).toBeNull()
  })

  it('propaga otros errores al consultar el consentimiento', async () => {
    const error = { response: { status: 500 } }
    api.get.mockRejectedValueOnce(error)
    await expect(obtenerMiConsentimiento()).rejects.toBe(error)
  })

  it('otorga el consentimiento en el backend', async () => {
    api.post.mockResolvedValueOnce({ data: { terms_version: 'v1.0' } })
    await otorgarConsentimiento()
    expect(api.post).toHaveBeenCalledWith('/wellbeing/consent', { terms_version: 'v1.0' })
  })

  it('envía la encuesta con el modelo del backend, sin datos de la cuenta (CU-23, RN-03)', async () => {
    api.post.mockResolvedValueOnce({ data: { crisis_detected: false } })
    await enviarRegistro({ animo: 4, texto: 'Tranquilo', barrio: 'Cuba' })
    expect(api.post).toHaveBeenCalledWith('/wellbeing/surveys', {
      neighborhood: 'Cuba',
      mood_score: 4,
      text: 'Tranquilo',
    })
  })

  it('pide las líneas de ayuda al backend (CU-27)', async () => {
    api.get.mockResolvedValueOnce({ data: { city: 'Pereira', helplines: [] } })
    expect(await obtenerLineasDeAyuda()).toEqual({ city: 'Pereira', helplines: [] })
    expect(api.get).toHaveBeenCalledWith('/wellbeing/helplines')
  })
})
