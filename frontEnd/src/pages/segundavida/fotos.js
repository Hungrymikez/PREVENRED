/**
 * Reglas de las fotos de una publicación de SegundaVida (CU-11 con CU-47).
 * Los formatos son los mismos que acepta el backend en POST /media/upload.
 */
export const MAXIMO_FOTOS = 5
export const TAMANO_MAXIMO_FOTO_MB = 10
export const TIPOS_FOTO = ['image/jpeg', 'image/png', 'image/webp']

/**
 * Agrega `nuevas` a las fotos `actuales` respetando las reglas (E1, E2 y A1 de CU-47).
 * Devuelve { fotos, error }: las fotos válidas que caben y, si alguna se rechazó, por qué.
 */
export function agregarFotos(actuales, nuevas) {
  const fotos = [...actuales]
  let error = ''

  for (const archivo of nuevas) {
    if (!TIPOS_FOTO.includes(archivo.type)) {
      error = 'Solo se permiten fotos JPG, PNG o WEBP.'
    } else if (archivo.size > TAMANO_MAXIMO_FOTO_MB * 1024 * 1024) {
      error = `Cada foto puede pesar máximo ${TAMANO_MAXIMO_FOTO_MB} MB.`
    } else if (fotos.length >= MAXIMO_FOTOS) {
      error = `Puedes agregar hasta ${MAXIMO_FOTOS} fotos.`
    } else {
      fotos.push(archivo)
    }
  }
  return { fotos, error }
}
