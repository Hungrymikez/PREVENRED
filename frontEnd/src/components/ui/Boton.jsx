import { LoaderCircle } from 'lucide-react'

const VARIANTES = {
  primario: 'bg-marca-600 text-white hover:bg-marca-700',
  secundario: 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-50',
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
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 font-medium transition focus-visible:ring-2 focus-visible:ring-marca-600 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTES[variante]} ${className}`}
      {...props}
    >
      {cargando && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
}
