import { Estrellas } from '@/components/ui/Estrellas'

/** Valoración del técnico (CU-15). Sin reseñas todavía no se muestra un 0. */
export function Valoracion({ tecnico }) {
  return tecnico.reviews_count > 0 ? (
    <Estrellas valor={tecnico.rating_average} total={tecnico.reviews_count} />
  ) : (
    <span className="text-sm text-slate-500 dark:text-slate-400">Sin reseñas todavía</span>
  )
}
