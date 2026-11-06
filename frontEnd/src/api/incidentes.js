/**
 * Reportes de emergencia (CU-29, CU-30, CU-31) y consulta de mis casos (CU-32).
 * DATOS DE PRUEBA: la versión real usa el backend (colecciones incidents y aid_needs).
 */
import { simularRed } from '@/api/mocks/simular'

/** Las tres clases de reporte y sus tipos. */
export const CATEGORIAS_REPORTE = {
  vivienda: {
    titulo: 'Daño en mi vivienda',
    cu: 'CU-29',
    tipos: {
      GRIETAS: 'Grietas en muros',
      TECHO_CAIDO: 'Techo o losa caída',
      VIVIENDA_INCLINADA: 'Vivienda inclinada',
      OTRO_DANO: 'Otro daño',
    },
  },
  via: {
    titulo: 'Vía bloqueada o escombros',
    cu: 'CU-30',
    tipos: {
      VIA_BLOQUEADA: 'Vía bloqueada',
      DESLIZAMIENTO: 'Deslizamiento',
      ARBOL_CAIDO: 'Árbol caído',
      OTRO_INCIDENTE: 'Otro incidente',
    },
  },
  ayuda: {
    titulo: 'Pedir ayuda',
    cu: 'CU-31',
    tipos: {
      AGUA: 'Agua',
      REFUGIO: 'Refugio',
      HERRAMIENTAS: 'Herramientas',
      APOYO_EMOCIONAL: 'Apoyo emocional',
      OTRA_NECESIDAD: 'Otra necesidad',
    },
  },
}

/** Los 5 estados autorizados que ve el ciudadano (RF-24). */
export const ESTADOS = ['REPORTADO', 'EN_REVISION', 'ASIGNADO', 'EN_ATENCION', 'RESUELTO']

export function nombreEstado(estado, categoria) {
  const nombres = {
    REPORTADO: 'Reportado',
    EN_REVISION: 'En revisión',
    ASIGNADO: 'Asignado',
    EN_ATENCION: 'En atención',
    // Para las vías el cierre se llama "Despejado" (CU-32).
    RESUELTO: categoria === 'via' ? 'Despejado' : 'Resuelto',
  }
  return nombres[estado]
}

export function nombreTipo(caso) {
  return CATEGORIAS_REPORTE[caso.categoria].tipos[caso.type]
}

const hace = (horas) => new Date(Date.now() - horas * 3_600_000).toISOString()

// Casos de prueba del usuario actual.
const misCasos = [
  {
    caseId: 'PR-2026-00041',
    categoria: 'via',
    type: 'DESLIZAMIENTO',
    description: 'Cayó tierra sobre la vía, solo pasa una moto.',
    coordenadas: [4.8205, -75.6702],
    quantity: null,
    status: 'ASIGNADO',
    reportedAt: hace(20),
    historial: [
      { toStatus: 'REPORTADO', changedAt: hace(20) },
      { toStatus: 'EN_REVISION', changedAt: hace(18) },
      { toStatus: 'ASIGNADO', changedAt: hace(6), note: 'Cuadrilla de obras públicas en camino.' },
    ],
  },
  {
    caseId: 'PR-2026-00027',
    categoria: 'ayuda',
    type: 'AGUA',
    description: '',
    coordenadas: [4.7965, -75.7295],
    quantity: 4,
    status: 'RESUELTO',
    reportedAt: hace(50),
    historial: [
      { toStatus: 'REPORTADO', changedAt: hace(50) },
      { toStatus: 'EN_REVISION', changedAt: hace(49) },
      { toStatus: 'ASIGNADO', changedAt: hace(40) },
      { toStatus: 'EN_ATENCION', changedAt: hace(30) },
      { toStatus: 'RESUELTO', changedAt: hace(26), note: 'Se entregaron 20 litros de agua.' },
    ],
  },
]

let consecutivo = 57

/**
 * Envía un reporte y devuelve el caso creado, con su número de seguimiento.
 * `clientId` y `reportedAt` llegan cuando el reporte se hizo sin conexión (CU-37).
 */
export async function crearReporte({
  categoria,
  type,
  description,
  quantity,
  coordenadas,
  clientId = crypto.randomUUID(),
  reportedAt = new Date().toISOString(),
}) {
  // Versión real: api.post('/incidents', ...) o api.post('/aid-needs', ...) según la categoría.
  // Igual que una petición real, falla si no hay conexión (sin "response", como axios).
  if (!navigator.onLine) throw new Error('Network Error')

  // El servidor hace upsert por clientId: un reintento devuelve el mismo caso (H-07).
  const existente = misCasos.find((c) => c.clientId === clientId)
  if (existente) return simularRed(existente, 300)

  consecutivo += 1
  const ahora = new Date().toISOString()
  const caso = {
    caseId: `PR-2026-${String(consecutivo).padStart(5, '0')}`,
    clientId,
    categoria,
    type,
    description: description?.trim() ?? '',
    quantity: categoria === 'ayuda' ? Number(quantity) : null,
    coordenadas,
    status: 'REPORTADO',
    reportedAt, // hora en que se hizo el reporte, aunque llegue después
    historial: [{ toStatus: 'REPORTADO', changedAt: ahora }],
  }
  misCasos.unshift(caso)
  return simularRed(caso, 700)
}

export function listarMisCasos() {
  return simularRed(misCasos)
}

/** Solo devuelve casos propios. El error no revela si el número existe para otra persona (E1). */
export async function obtenerCaso(caseId) {
  const caso = misCasos.find((c) => c.caseId === caseId.trim().toUpperCase())
  if (!caso)
    throw new Error('No encontramos ese número entre tus casos. Revisa que esté bien escrito.')
  return simularRed(caso)
}
