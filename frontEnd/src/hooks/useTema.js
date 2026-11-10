import { useSyncExternalStore } from 'react'

export const TEMA_KEY = 'prevenred_tema'

/** Tema guardado; si la persona nunca eligió, el que use su celular o computador. */
function temaInicial() {
  try {
    const guardado = localStorage.getItem(TEMA_KEY)
    if (guardado === 'claro' || guardado === 'oscuro') return guardado
  } catch {
    // Sin almacenamiento: se usa el del sistema.
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'oscuro' : 'claro'
}

// Un solo tema para toda la app: todos los componentes que usan useTema se enteran del cambio.
let temaActual = temaInicial()
const suscriptores = new Set()

/** Marca el documento: las clases dark: de Tailwind se activan con data-tema="oscuro". */
function aplicar(tema) {
  document.documentElement.dataset.tema = tema
}
aplicar(temaActual)

function cambiarTema(nuevo) {
  temaActual = nuevo
  aplicar(nuevo)
  try {
    localStorage.setItem(TEMA_KEY, nuevo)
  } catch {
    // Sin almacenamiento: el cambio dura hasta recargar.
  }
  suscriptores.forEach((avisar) => avisar())
}

function suscribirse(avisar) {
  suscriptores.add(avisar)
  return () => suscriptores.delete(avisar)
}

/** Solo para pruebas: vuelve a leer el tema guardado. */
export function reiniciarTema() {
  temaActual = temaInicial()
  aplicar(temaActual)
  suscriptores.forEach((avisar) => avisar())
}

/**
 * Tema claro u oscuro de la app, elegido por la persona; se recuerda entre visitas.
 * Devuelve { tema: 'claro' | 'oscuro', oscuro, alternar }.
 */
export function useTema() {
  const tema = useSyncExternalStore(suscribirse, () => temaActual)
  return {
    tema,
    oscuro: tema === 'oscuro',
    alternar: () => cambiarTema(tema === 'oscuro' ? 'claro' : 'oscuro'),
  }
}
