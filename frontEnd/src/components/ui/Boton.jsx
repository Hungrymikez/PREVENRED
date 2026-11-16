import { LoaderCircle } from 'lucide-react'

const VARIANTES = {
  primario:
    'bg-marca-600 text-white hover:bg-marca-700 dark:bg-amber-500 dark:text-slate-950 dark:hover:bg-amber-400',
  secundario:
    'border border-slate-300 bg-white text-slate-800 hover:bg-slate-50 dark:border-white/20 dark:bg-white/10 dark:text-white dark:hover:bg-white/15',
  peligro: 'bg-alerta-600 text-white hover:bg-alerta-700',
  exito: 'bg-green-600 text-white hover:bg-green-700',
}

/**
 * Botón base de la app.
 * - variante: "primario" | "secundario" | "peligro" | "exito"
 * - cargando: muestra un spinner y desactiva el botón (útil mientras se envía un formulario)
 */
export function Boton({
  variante = 'primario',
  cargando = false,
  disabled,
  className = '',
  children,
  ...props
}) {
  return (
    <button
      disabled={disabled || cargando}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 font-medium transition focus-visible:ring-2 focus-visible:ring-marca-600 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:focus-visible:ring-amber-400 dark:focus-visible:ring-offset-slate-950 ${VARIANTES[variante]} ${className}`}
      {...props}
    >
      {cargando && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
}
