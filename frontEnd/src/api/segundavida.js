/**
 * SegundaVida (CU-11, CU-12). DATOS DE PRUEBA: cuando el backend tenga el módulo marketplace,
 * cada función pasa a llamar a la API (ej.: api.get('/materials', { params: filtros })).
 */
import { PUBLICACIONES } from '@/api/mocks/datos'
import { simularRed } from '@/api/mocks/simular'
import { CENTRO_PEREIRA } from '@/utils/mapa'
import { coordenadasDeZona } from '@/utils/zonas'
import { distanciaKm } from '@/utils/distancia'

export const MODALIDADES = {
  VENTA: { pestana: 'Comprar', nombre: 'Venta' },
  INTERCAMBIO: { pestana: 'Intercambiar', nombre: 'Intercambio' },
  ALQUILER: { pestana: 'Alquilar', nombre: 'Alquiler' },
}

export const CATEGORIAS = [
  'Construcción',
  'Madera',
  'Eléctrico',
  'Plomería',
  'Pintura',
  'Herramientas',
]

export const CONDICIONES = {
  nuevo: 'Nuevo',
  buen_estado: 'Buen estado',
  usado: 'Usado',
}

const publicaciones = [...PUBLICACIONES]

/** Agrega coordenadas aproximadas y distancia desde `origen`. */
function conUbicacion(p, origen) {
  const coordenadas = coordenadasDeZona(p.zona)
  return { ...p, coordenadas, distanciaKm: distanciaKm(origen, coordenadas) }
}

/** Filtra y ordena por cercanía. Se exporta para probarla sin la demora simulada. */
export function filtrarPublicaciones(lista, filtros = {}, origen = CENTRO_PEREIRA) {
  const { modalidad, categoria, condicion, precioMax, texto } = filtros
  const buscado = texto?.trim().toLowerCase()

  return lista
    .filter((p) => !modalidad || p.offerType === modalidad)
    .filter((p) => !categoria || p.category === categoria)
    .filter((p) => !condicion || p.condition === condicion)
    .filter((p) => !precioMax || p.price <= Number(precioMax))
    .filter((p) => !buscado || `${p.title} ${p.description}`.toLowerCase().includes(buscado))
    .map((p) => conUbicacion(p, origen))
    .sort((a, b) => a.distanciaKm - b.distanciaKm)
}

export function listarPublicaciones(filtros) {
  return simularRed(filtrarPublicaciones(publicaciones, filtros))
}

export async function obtenerPublicacion(id) {
  const publicacion = publicaciones.find((p) => p.id === id)
  if (!publicacion) throw new Error('La publicación no existe.')
  return simularRed(conUbicacion(publicacion, CENTRO_PEREIRA))
}

/** CU-11. En la versión real se envían también las imágenes (CU-47). */
export function publicar(datos, autor) {
  const nueva = {
    ...datos,
    id: `m${Date.now()}`,
    tipo: datos.category === 'Herramientas' ? 'herramienta' : 'material',
    price: datos.offerType === 'INTERCAMBIO' ? 0 : Number(datos.price),
    quantity: Number(datos.quantity),
    ownerName: autor,
    createdAt: new Date().toISOString().slice(0, 10),
  }
  publicaciones.unshift(nueva)
  return simularRed(nueva)
}
