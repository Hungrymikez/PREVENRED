/**
 * SegundaVida (CU-11, CU-12), conectado al backend (contexto marketplace, colección materials):
 *  - Publicar            -> POST /marketplace/materials (fotos subidas antes con CU-47)
 *  - Buscar por cercanía -> GET  /marketplace/materials/search (exige un punto: lon/lat)
 *  - Detalle             -> GET  /marketplace/materials/{id}
 * Las pantallas usan una forma propia de la "publicación"; aquí se traduce desde y hacia la API.
 */
import { api, mensajeDeError } from '@/api/client'
import { subirArchivo, urlPublica } from '@/api/media'
import { distanciaKm } from '@/utils/distancia'
import { CENTRO_PEREIRA } from '@/utils/mapa'
import { coordenadasDeZona, NOMBRES_ZONAS, ZONAS } from '@/utils/zonas'

/** Tipos de oferta del backend (OfferType). En una donación el precio siempre es 0. */
export const MODALIDADES = {
  VENTA: { pestana: 'Comprar', nombre: 'Venta' },
  DONACION: { pestana: 'Donaciones', nombre: 'Donación' },
  ALQUILER: { pestana: 'Alquilar', nombre: 'Alquiler' },
}

/** Categorías del backend (MaterialCategory) con su nombre en pantalla. */
export const CATEGORIAS = {
  CONSTRUCCION: 'Construcción',
  MADERA: 'Madera',
  METAL: 'Metal',
  ELECTRICO: 'Eléctrico',
  PLOMERIA: 'Plomería',
  HERRAMIENTAS: 'Herramientas',
  OTROS: 'Otros',
}

/** Estados del backend (MaterialCondition). */
export const CONDICIONES = {
  NUEVO: 'Nuevo',
  BUENO: 'Buen estado',
  USADO: 'Usado',
}

/** Unidades sugeridas para la cantidad (el backend guarda texto libre en minúsculas). */
export const UNIDADES = ['unidades', 'metros', 'm²', 'kg', 'bultos', 'litros']

/** Radio de búsqueda: toda Pereira cabe en 20 km (el backend admite hasta 50 km). */
const RADIO_BUSQUEDA_METROS = 20000
/** Más allá de esta distancia del centro de un barrio, se muestra solo "Pereira". */
const DISTANCIA_MAXIMA_BARRIO_KM = 2

/**
 * Barrio más cercano a un punto: la publicación solo muestra el barrio, nunca la
 * dirección exacta (CU-11, RN-05).
 */
export function barrioCercano(coordenadas) {
  let mejor = null
  for (const zona of ZONAS) {
    const km = distanciaKm(coordenadas, zona.coordenadas)
    if (!mejor || km < mejor.km) mejor = { nombre: zona.nombre, km }
  }
  return mejor && mejor.km <= DISTANCIA_MAXIMA_BARRIO_KM ? mejor.nombre : 'Pereira'
}

/** Punto desde el que se busca: el barrio elegido o el centro de Pereira. */
export function origenDeBusqueda(barrio) {
  return NOMBRES_ZONAS.includes(barrio) ? coordenadasDeZona(barrio) : CENTRO_PEREIRA
}

/** Material del backend -> publicación de la pantalla. */
export function dePublicacion(m, origen = CENTRO_PEREIRA) {
  const coordenadas = [m.latitude, m.longitude]
  return {
    id: m.id,
    title: m.title,
    description: m.description,
    category: m.category,
    offerType: m.offer_type,
    condition: m.condition,
    quantity: m.quantity,
    unit: m.unit,
    price: m.price ?? 0,
    coordenadas,
    zona: barrioCercano(coordenadas),
    distanciaKm: distanciaKm(origen, coordenadas),
    ownerName: m.owner_name || 'Un vecino',
    mediaUrls: (m.media_urls ?? []).map(urlPublica),
    createdAt: m.created_at,
  }
}

/**
 * Filtros que el backend aún no resuelve (estado, precio máximo y texto) y orden por
 * cercanía. Se exporta para probarla sin red.
 */
export function filtrarPublicaciones(lista, filtros = {}) {
  const { condicion, precioMax, texto } = filtros
  const buscado = texto?.trim().toLowerCase()

  return lista
    .filter((p) => !condicion || p.condition === condicion)
    .filter((p) => !precioMax || p.price <= Number(precioMax))
    .filter((p) => !buscado || `${p.title} ${p.description}`.toLowerCase().includes(buscado))
    .sort((a, b) => a.distanciaKm - b.distanciaKm)
}

/** CU-12. `filtros`: { modalidad, categoria, condicion, precioMax, texto, cerca }. */
export async function listarPublicaciones(filtros = {}) {
  const origen = origenDeBusqueda(filtros.cerca)
  try {
    const { data } = await api.get('/marketplace/materials/search', {
      params: {
        latitude: origen[0],
        longitude: origen[1],
        radius_meters: RADIO_BUSQUEDA_METROS,
        offer_type: filtros.modalidad || undefined,
        category: filtros.categoria || undefined,
        limit: 100,
      },
    })
    return filtrarPublicaciones(
      data.map((m) => dePublicacion(m, origen)),
      filtros,
    )
  } catch (error) {
    throw new Error(mensajeDeError(error))
  }
}

/** CU-12, pasos 6-7. */
export async function obtenerPublicacion(id) {
  try {
    const { data } = await api.get(`/marketplace/materials/${encodeURIComponent(id)}`)
    return dePublicacion(data)
  } catch (error) {
    if (error.response?.status === 404) throw new Error('La publicación no existe.')
    throw new Error(mensajeDeError(error))
  }
}

/**
 * CU-11. `fotos` son los archivos elegidos (opcional): cada una se sube con
 * POST /media/upload (CU-47) y la publicación guarda sus URLs en `media_urls`.
 * La ubicación que se envía es el centro del barrio elegido, nunca la dirección.
 */
export async function publicar(datos, fotos = []) {
  try {
    const mediaUrls = []
    for (const foto of fotos) mediaUrls.push(await subirArchivo(foto))

    const [latitude, longitude] = coordenadasDeZona(datos.zona)
    const { data } = await api.post('/marketplace/materials', {
      title: datos.title.trim(),
      description: datos.description.trim(),
      category: datos.category,
      offer_type: datos.offerType,
      condition: datos.condition,
      quantity: Number(datos.quantity),
      unit: datos.unit,
      price: datos.offerType === 'DONACION' ? null : Number(datos.price),
      longitude,
      latitude,
      media_urls: mediaUrls,
    })
    return dePublicacion(data)
  } catch (error) {
    throw new Error(mensajeDeError(error))
  }
}
