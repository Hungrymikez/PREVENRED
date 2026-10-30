/** Simula la demora de una petición real, para ver los estados de carga en pantalla. */
export function simularRed(valor, ms = 400) {
  return new Promise((resolver) => setTimeout(() => resolver(structuredClone(valor)), ms))
}
