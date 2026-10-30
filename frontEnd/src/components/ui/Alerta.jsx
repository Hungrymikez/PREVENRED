import { CircleAlert, CircleCheck, Info } from 'lucide-react'

const TIPOS = {
  error: { estilo: 'border-alerta-600 bg-alerta-50 text-alerta-700', Icono: CircleAlert },
  exito: { estilo: 'border-green-600 bg-green-50 text-green-800', Icono: CircleCheck },
  info: { estilo: 'border-marca-600 bg-marca-50 text-marca-900', Icono: Info },
}

/** Mensaje destacado. tipo: "error" | "exito" | "info". */
export function Alerta({ tipo = 'info', children }) {
  const { estilo, Icono } = TIPOS[tipo]

  return (
    <div
      role={tipo === 'error' ? 'alert' : 'status'}
      className={`flex items-start gap-2 rounded-lg border-l-4 p-3 text-sm ${estilo}`}
    >
      <Icono className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}
