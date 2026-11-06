import { Star } from 'lucide-react'

/** Valoración de 1 a 5 (CU-15). Muestra la estrella y el número; el lector de pantalla lo lee completo. */
export function Estrellas({ valor, total }) {
  return (
    <span className="inline-flex items-center gap-1 text-sm text-slate-700">
      <Star className="size-4 fill-amber-400 text-amber-400" aria-hidden="true" />
      <span className="sr-only">Valoración: </span>
      <span className="font-medium">
        {valor.toLocaleString('es-CO', { minimumFractionDigits: 1 })}
      </span>
      {total !== undefined && <span className="text-slate-500">({total} reseñas)</span>}
    </span>
  )
}
