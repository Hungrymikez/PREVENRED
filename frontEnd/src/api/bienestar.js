/**
 * Mente Resiliente (CU-23, CU-24, CU-27). Conectado al backend real (/wellbeing).
 * Privacidad (RN-03): la encuesta NO se guarda con el usuario, solo con su barrio, el nivel de
 * ánimo y el texto (el backend enmascara datos personales antes de guardarlo).
 */
import { api } from '@/api/client'

/** Versión del aviso de consentimiento que acepta la persona (wellbeing_consents). */
export const VERSION_CONSENTIMIENTO = 'v1.0'

/** Máximo de caracteres del texto libre (igual que el backend). */
export const MAX_TEXTO = 1000

export const NIVELES_ANIMO = [
  { valor: 5, nombre: 'Muy bien', emoji: '😄' },
  { valor: 4, nombre: 'Bien', emoji: '🙂' },
  { valor: 3, nombre: 'Regular', emoji: '😐' },
  { valor: 2, nombre: 'Mal', emoji: '🙁' },
  { valor: 1, nombre: 'Muy mal', emoji: '😢' },
]

/**
 * CU-24. Consentimiento vigente de quien consulta, o null si aún no lo ha dado
 * (el backend responde 404 si no existe o fue revocado).
 */
export async function obtenerMiConsentimiento() {
  try {
    const { data } = await api.get('/wellbeing/consent/me')
    return data
  } catch (error) {
    if (error?.response?.status === 404) return null
    throw error
  }
}

/** CU-24. Lo guarda el backend en wellbeing_consents (uno por usuario). */
export async function otorgarConsentimiento() {
  const { data } = await api.post('/wellbeing/consent', {
    terms_version: VERSION_CONSENTIMIENTO,
  })
  return data
}

/**
 * CU-23. Envía { neighborhood, mood_score (1-5), text? }. Devuelve, entre otros,
 * `crisis_detected` y `crisis_support_message` (RF-18: canalización inmediata).
 */
export async function enviarRegistro({ animo, texto, barrio }) {
  const { data } = await api.post('/wellbeing/surveys', {
    neighborhood: barrio,
    mood_score: animo,
    text: texto ?? '',
  })
  return data
}

/** CU-27. Líneas de ayuda oficiales: { city, helplines: [{ name, phone, type }] }. */
export async function obtenerLineasDeAyuda() {
  const { data } = await api.get('/wellbeing/helplines')
  return data
}
