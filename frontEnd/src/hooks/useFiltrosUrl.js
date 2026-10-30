import { useSearchParams } from 'react-router'

/**
 * Guarda los filtros de una búsqueda en la URL (?categoria=Pintura&vista=mapa).
 * Así, al volver desde un detalle o compartir el enlace, los filtros se conservan.
 */
export function useFiltrosUrl() {
  const [parametros, setParametros] = useSearchParams()
  const filtros = Object.fromEntries(parametros)

  function cambiar(nombre, valor) {
    setParametros(
      (actuales) => {
        const nuevos = new URLSearchParams(actuales)
        if (valor === '' || valor === undefined || valor === false) nuevos.delete(nombre)
        else nuevos.set(nombre, valor)
        return nuevos
      },
      { replace: true },
    )
  }

  return [filtros, cambiar]
}
