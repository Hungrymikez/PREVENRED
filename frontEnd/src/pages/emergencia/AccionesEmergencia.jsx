import { ChevronRight, Construction, HandHelping, House } from 'lucide-react'
import { Link } from 'react-router'
import { CATEGORIAS_REPORTE } from '@/api/incidentes'

const ICONOS = { vivienda: House, via: Construction, ayuda: HandHelping }

/** Los tres botones grandes de reporte: primera de las 3 interacciones (RNF-10). */
export function AccionesEmergencia() {
  return (
    <ul className="grid gap-3 sm:grid-cols-3">
      {Object.entries(CATEGORIAS_REPORTE).map(([clave, { titulo }]) => {
        const Icono = ICONOS[clave]
        return (
          <li key={clave}>
            <Link
              to={`/emergencia/reportar/${clave}`}
              className="flex h-full items-center gap-3 rounded-2xl border-2 border-alerta-600 bg-white p-4 font-semibold text-slate-900 transition hover:bg-alerta-50 sm:flex-col sm:items-start"
            >
              <Icono className="size-8 shrink-0 text-alerta-600" aria-hidden="true" />
              <span className="flex-1">{titulo}</span>
              <ChevronRight className="size-5 text-slate-400 sm:hidden" aria-hidden="true" />
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
