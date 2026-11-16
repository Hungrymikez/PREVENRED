/**
 * Reportes de emergencia (CU-29, CU-30, CU-31) y consulta de mis casos (CU-32).
 * Conectado al backend real:
 *  - Daño en vivienda y vías  -> POST /incidents/        (colección incidents)
 *    con su foto opcional subida antes con POST /media/upload (CU-47)
 *  - Pedir ayuda              -> POST /aid/needs         (colección aid_needs)
 *  - Mis casos                -> GET /incidents/ + GET /aid/needs/mine (solo los propios)
 *  - Detalle con historial    -> GET /incidents/case/{número}
 * Las pantallas usan una forma propia del "caso"; aquí se traduce desde y hacia la API.
 */
import { api, mensajeDeError } from '@/api/client'
import { subirArchivo } from '@/api/media'

/**
 * Las tres clases de reporte. Cada tipo de la pantalla indica a qué tipo del backend
 * corresponde (`api`); el detalle (p. ej. "Grietas en muros") viaja en la descripción.
 */
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
    api: {
      GRIETAS: 'VIVIENDA_DANADA',
      TECHO_CAIDO: 'VIVIENDA_DANADA',
      VIVIENDA_INCLINADA: 'VIVIENDA_DANADA',
      OTRO_DANO: 'VIVIENDA_DANADA',
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
    api: {
      VIA_BLOQUEADA: 'VIA_BLOQUEADA',
      DESLIZAMIENTO: 'DESLIZAMIENTO',
      ARBOL_CAIDO: 'VIA_BLOQUEADA',
      OTRO_INCIDENTE: 'OTRO',
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
    api: {
      AGUA: 'AGUA',
      REFUGIO: 'REFUGIO',
      HERRAMIENTAS: 'HERRAMIENTAS',
      APOYO_EMOCIONAL: 'OTROS',
      OTRA_NECESIDAD: 'OTROS',
    },
  },
}

/** Nombres de los tipos del backend, para casos creados desde otra pantalla o versión. */
const TIPOS_BACKEND = {
  VIVIENDA_DANADA: 'Vivienda dañada',
  DANO_ESTRUCTURAL: 'Daño estructural',
  VIA_BLOQUEADA: 'Vía bloqueada',
  DESLIZAMIENTO: 'Deslizamiento',
  INUNDACION: 'Inundación',
  OTRO: 'Otro',
  ALIMENTOS: 'Alimentos',
  AGUA: 'Agua',
  HERRAMIENTAS: 'Herramientas',
  REFUGIO: 'Refugio',
  ROPA: 'Ropa',
  PRIMEROS_AUXILIOS: 'Primeros auxilios',
  OTROS: 'Otra necesidad',
}

/** Los 5 estados autorizados que ve el ciudadano (RF-24), iguales a los del backend. */
export const ESTADOS = ['REPORTADO', 'EN_REVISION', 'ASIGNADO', 'EN_ATENCION', 'RESUELTO']

/** Estados de aid_needs -> estados que ve el ciudadano. */
const ESTADO_AYUDA = {
  PENDIENTE: 'REPORTADO',
  EMPAREJADO: 'ASIGNADO',
  ENTREGADO: 'RESUELTO',
  CANCELADO: 'RESUELTO',
}

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
  return (
    CATEGORIAS_REPORTE[caso.categoria]?.tipos[caso.type] ?? TIPOS_BACKEND[caso.type] ?? caso.type
  )
}

const PREFIJO_AYUDA = 'AY-'
const NO_ENCONTRADO = 'No encontramos ese número entre tus casos. Revisa que esté bien escrito.'

/** Incidente del backend -> caso de la pantalla. */
function deIncidente(i) {
  const vivienda = ['VIVIENDA_DANADA', 'DANO_ESTRUCTURAL'].includes(i.incident_type)
  return {
    id: i.id,
    caseId: i.case_number,
    categoria: vivienda ? 'vivienda' : 'via',
    type: i.incident_type,
    description: i.description,
    coordenadas: [i.latitude, i.longitude],
    quantity: null,
    status: i.status,
    reportedAt: i.reported_at ?? i.created_at,
    historial: [
      { toStatus: 'REPORTADO', changedAt: i.reported_at ?? i.created_at },
      ...(i.history ?? []).map((h) => ({
        toStatus: h.to_status,
        changedAt: h.changed_at,
        note: h.notes,
      })),
    ],
  }
}

/** Solicitud de ayuda (aid_needs) -> caso de la pantalla. */
function deAyuda(n) {
  const tipo =
    Object.entries(CATEGORIAS_REPORTE.ayuda.api).find(([, cat]) => cat === n.category)?.[0] ??
    n.category
  return {
    id: n.id,
    // aid_needs aún no tiene consecutivo propio (caseId): se muestra uno derivado del id.
    caseId: `${PREFIJO_AYUDA}${n.id.slice(-6).toUpperCase()}`,
    categoria: 'ayuda',
    type: tipo,
    description: n.title,
    coordenadas: [n.latitude, n.longitude],
    quantity: n.quantity,
    status: ESTADO_AYUDA[n.status] ?? 'REPORTADO',
    reportedAt: n.created_at,
    historial: [{ toStatus: 'REPORTADO', changedAt: n.created_at }],
  }
}

/** "Grietas en muros: la pared se partió" (el tipo exacto queda en la descripción). */
function describir(etiqueta, texto) {
  const detalle = texto?.trim()
  return detalle ? `${etiqueta}: ${detalle}` : etiqueta
}

/**
 * Envía un reporte y devuelve el caso creado, con su número de seguimiento.
 * `clientId` y `reportedAt` llegan cuando el reporte se hizo sin conexión (CU-37): con el
 * mismo clientId el backend devuelve el mismo caso en vez de duplicarlo.
 * `foto` (File o Blob, opcional) se sube primero con CU-47 y viaja en `media_urls`; los
 * reportes guardados sin conexión también la traen. Las solicitudes de ayuda no llevan foto.
 */
export async function crearReporte({
  categoria,
  type,
  description,
  quantity,
  coordenadas,
  foto = null,
  clientId = crypto.randomUUID(),
  reportedAt = new Date().toISOString(),
}) {
  // Sin conexión falla como una petición real (sin "response"): el reporte se guarda local.
  if (!navigator.onLine) throw new Error('Network Error')

  const config = CATEGORIAS_REPORTE[categoria]
  const etiqueta = config.tipos[type]
  const [latitude, longitude] = coordenadas

  if (categoria === 'ayuda') {
    const { data } = await api.post('/aid/needs', {
      title: describir(etiqueta, description),
      category: config.api[type],
      quantity: Number(quantity),
      unit: 'personas',
      priority: 'ALTA',
      longitude,
      latitude,
    })
    return deAyuda(data)
  }

  // Si la subida falla por falta de red, el error no trae "response" y el reporte se guarda local.
  const mediaUrls = foto ? [await subirArchivo(foto)] : []

  const { data } = await api.post('/incidents/', {
    incident_type: config.api[type],
    severity: 'MEDIA',
    description: describir(etiqueta, description),
    longitude,
    latitude,
    media_urls: mediaUrls,
    client_id: clientId,
    reported_at: reportedAt,
  })
  return deIncidente(data)
}

/** CU-32: solo los casos de la persona con sesión (el backend filtra por dueño). */
export async function listarMisCasos() {
  const [incidentes, ayudas] = await Promise.all([
    api.get('/incidents/', { params: { limit: 100 } }),
    api.get('/aid/needs/mine'),
  ])
  return [...incidentes.data.map(deIncidente), ...ayudas.data.map(deAyuda)].sort((a, b) =>
    b.reportedAt.localeCompare(a.reportedAt),
  )
}

/** Solo devuelve casos propios. El error no revela si el número existe para otra persona (E1). */
export async function obtenerCaso(caseId) {
  const numero = caseId.trim().toUpperCase()
  try {
    if (numero.startsWith(PREFIJO_AYUDA)) {
      const { data } = await api.get('/aid/needs/mine')
      const caso = data.map(deAyuda).find((c) => c.caseId === numero)
      if (!caso) throw Object.assign(new Error(NO_ENCONTRADO), { noEncontrado: true })
      return caso
    }
    const { data } = await api.get(`/incidents/case/${encodeURIComponent(numero)}`)
    return deIncidente(data)
  } catch (error) {
    if (error.noEncontrado || error.response?.status === 404) throw new Error(NO_ENCONTRADO)
    throw new Error(mensajeDeError(error))
  }
}
