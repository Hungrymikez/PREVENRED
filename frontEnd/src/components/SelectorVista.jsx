import { List, Map } from 'lucide-react'

const OPCIONES = [
  { valor: 'lista', nombre: 'Lista', Icono: List },
  { valor: 'mapa', nombre: 'Mapa', Icono: Map },
]

/** Cambia entre ver los resultados en lista o en el mapa. */
export function SelectorVista({ vista, onCambiar }) {
  return (
    <div
      className="inline-flex rounded-lg border border-slate-300 bg-white p-0.5 dark:border-white/20 dark:bg-slate-900"
      role="group"
    >
      {OPCIONES.map(({ valor, nombre, Icono }) => (
        <button
          key={valor}
          type="button"
          aria-pressed={vista === valor}
          onClick={() => onCambiar(valor)}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 aria-pressed:bg-marca-600 aria-pressed:text-white dark:text-slate-200 dark:aria-pressed:bg-amber-500 dark:aria-pressed:text-slate-950"
        >
          <Icono className="size-4" aria-hidden="true" />
          {nombre}
        </button>
      ))}
    </div>
  )
}
