/**
 * Mente Resiliente (CU-23, CU-24, CU-27). DATOS DE PRUEBA: cuando el backend tenga el módulo
 * wellbeing, cada función pasa a llamar a la API.
 * Privacidad (RN-03): la respuesta NO se guarda con el usuario, solo con su barrio y la fecha.
 */
import { simularRed } from '@/api/mocks/simular'

const CLAVE_CONSENTIMIENTO = 'prevenred_consentimiento_bienestar'

export const NIVELES_ANIMO = [
  { valor: 5, nombre: 'Muy bien', emoji: '😄' },
  { valor: 4, nombre: 'Bien', emoji: '🙂' },
  { valor: 3, nombre: 'Regular', emoji: '😐' },
  { valor: 2, nombre: 'Mal', emoji: '🙁' },
  { valor: 1, nombre: 'Muy mal', emoji: '😢' },
]

/** CU-24. Versión real: lo guarda el backend en wellbeing_consents. */
export function tieneConsentimiento() {
  try {
    return localStorage.getItem(CLAVE_CONSENTIMIENTO) === 'v1'
  } catch {
    return false
  }
}

export function otorgarConsentimiento() {
  try {
    localStorage.setItem(CLAVE_CONSENTIMIENTO, 'v1')
  } catch {
    // Sin almacenamiento disponible: se pedirá de nuevo la próxima vez.
  }
  return simularRed(true, 200)
}

/** CU-23. Solo se envía { animo, texto, barrio }: el nivel de ánimo, el texto opcional y el barrio. */
// Versión real: api.post('/wellbeing/surveys', { answers: { animo, texto }, zone: barrio })
export function enviarRegistro() {
  return simularRed({ recibido: true })
}

/** CU-27. El número oficial de la línea de apoyo está por confirmar (doc 05, E1). */
export const LINEAS_DE_APOYO = [
  {
    nombre: 'Línea de emergencias',
    detalle: 'Si tú o alguien está en peligro inmediato.',
    telefono: '123',
  },
  {
    nombre: 'Línea de apoyo en salud mental',
    detalle: 'Número oficial por confirmar con la Secretaría de Salud de Pereira.',
    telefono: null,
  },
]
