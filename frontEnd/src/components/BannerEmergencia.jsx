import { Siren } from 'lucide-react'
import { Link } from 'react-router'
import { TIPOS_EVENTO } from '@/api/modo'

/** Aviso visible en todas las pantallas mientras el Modo Emergencia está activo (RF-02). */
export function BannerEmergencia({ modo }) {
  return (
    <div className="bg-alerta-700 text-white" role="region" aria-label="Aviso de emergencia">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-2.5">
        <p className="flex items-center gap-2 text-sm">
          <Siren className="size-5 shrink-0" aria-hidden="true" />
          <span>
            <strong>Modo Emergencia · {TIPOS_EVENTO[modo.eventType] ?? 'Emergencia'}.</strong>{' '}
            {modo.reason}
          </span>
        </p>
        <Link
          to="/emergencia"
          className="rounded-lg bg-white px-3 py-1.5 text-sm font-semibold text-alerta-700 hover:bg-alerta-50"
        >
          Reportar
        </Link>
      </div>
    </div>
  )
}
