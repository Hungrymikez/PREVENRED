import { LoaderCircle, SearchX } from 'lucide-react'
import { mensajeDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'

/** Estados de una lista: cargando, error o sin resultados. */
export function Cargando({ texto = 'Cargando…' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-slate-600" role="status">
      <LoaderCircle className="size-5 animate-spin text-marca-600" aria-hidden="true" />
      {texto}
    </div>
  )
}

export function ErrorAlCargar({ error }) {
  return <Alerta tipo="error">{error?.message ?? mensajeDeError(error)}</Alerta>
}

export function SinResultados({ titulo = 'Sin resultados', children }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-4 py-10 text-center">
      <SearchX className="mx-auto size-8 text-slate-400" aria-hidden="true" />
      <p className="mt-2 font-medium text-slate-900">{titulo}</p>
      {children && <p className="mt-1 text-sm text-slate-600">{children}</p>}
    </div>
  )
}
