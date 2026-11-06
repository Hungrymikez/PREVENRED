import { ClipboardList } from 'lucide-react'
import { Link } from 'react-router'
import { AccionesEmergencia } from './AccionesEmergencia'

/** Pantalla principal de emergencia: elegir qué reportar. */
export default function Emergencia() {
  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900">¿Qué quieres reportar?</h1>
      <p className="mt-1 text-slate-600">Tu reporte llega a los coordinadores de la emergencia.</p>

      <div className="mt-6">
        <AccionesEmergencia />
      </div>

      <Link
        to="/emergencia/casos"
        className="mt-6 inline-flex items-center gap-2 font-medium text-marca-700 hover:underline"
      >
        <ClipboardList className="size-5" aria-hidden="true" />
        Ver el estado de mis casos
      </Link>
    </>
  )
}
