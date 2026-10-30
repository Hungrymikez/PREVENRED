/**
 * Barrios de Pereira con un punto aproximado (centro del barrio).
 * Se usa para mostrar ubicaciones aproximadas: nunca la dirección exacta (CU-11, RN-05).
 */
export const ZONAS = [
  { nombre: 'Centro', coordenadas: [4.8133, -75.6961] },
  { nombre: 'Cuba', coordenadas: [4.796, -75.731] },
  { nombre: 'Boston', coordenadas: [4.809, -75.683] },
  { nombre: 'Villasantana', coordenadas: [4.825, -75.665] },
  { nombre: 'Álamos', coordenadas: [4.792, -75.74] },
  { nombre: 'Kennedy', coordenadas: [4.818, -75.703] },
  { nombre: 'San Joaquín', coordenadas: [4.79, -75.735] },
  { nombre: 'El Jardín', coordenadas: [4.797, -75.72] },
  { nombre: 'Pinares', coordenadas: [4.808, -75.688] },
]

export const NOMBRES_ZONAS = ZONAS.map((z) => z.nombre)

export function coordenadasDeZona(nombre) {
  return ZONAS.find((z) => z.nombre === nombre)?.coordenadas ?? ZONAS[0].coordenadas
}
