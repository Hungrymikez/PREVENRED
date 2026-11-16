import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { listarAuditoria } from '@/api/admin'
import { mensajeDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'
import { Cargando, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { formatearFecha } from '@/utils/fechas'

/** Recursos auditados más comunes (el backend los guarda en minúsculas). */
const RECURSOS = {
  incidents: 'Incidentes',
  users: 'Usuarios',
  property_inspections: 'Inspecciones',
  aid_needs: 'Ayudas',
}

const LIMITES = [50, 100, 200]

/**
 * CU-09 · Consultar auditoría. Solo el Administrador ve quién hizo qué, sobre qué recurso
 * y cuándo. Los registros llegan del más reciente al más antiguo.
 */
export default function Auditoria() {
  const [recurso, setRecurso] = useState('')
  const [limite, setLimite] = useState(50)
  const {
    data: registros = [],
    isPending,
    error,
  } = useQuery({
    queryKey: ['admin', 'auditoria', recurso, limite],
    queryFn: () => listarAuditoria({ recurso, limite }),
  })

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Registro de auditoría</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Acciones sensibles realizadas en la plataforma. Más recientes primero.
      </p>

      <div className="mt-5 flex flex-wrap items-end gap-3">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por recurso">
          {[['', 'Todos'], ...Object.entries(RECURSOS)].map(([valor, nombre]) => (
            <button
              key={valor || 'todos'}
              type="button"
              aria-pressed={recurso === valor}
              onClick={() => setRecurso(valor)}
              className="rounded-full border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100 aria-pressed:border-marca-600 aria-pressed:bg-marca-600 aria-pressed:text-white dark:border-white/20 dark:text-slate-200 dark:hover:bg-white/10 dark:aria-pressed:border-amber-500 dark:aria-pressed:bg-amber-500 dark:aria-pressed:text-slate-950"
            >
              {nombre}
            </button>
          ))}
        </div>
        <label className="ml-auto flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
          Mostrar
          <select
            value={limite}
            onChange={(e) => setLimite(Number(e.target.value))}
            className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-slate-900 dark:border-white/20 dark:bg-slate-900 dark:text-white"
          >
            {LIMITES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-5">
        {isPending ? (
          <Cargando texto="Cargando registros…" />
        ) : error ? (
          <Alerta tipo="error">{mensajeDeError(error)}</Alerta>
        ) : registros.length === 0 ? (
          <SinResultados titulo="Sin registros">
            {recurso
              ? `No hay acciones registradas sobre «${RECURSOS[recurso]}».`
              : 'Cuando haya acciones auditadas, aparecerán aquí.'}
          </SinResultados>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-600 dark:border-white/10 dark:text-slate-300">
                <tr>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Fecha
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Acción
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Recurso
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Responsable
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Detalle
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                {registros.map((r) => (
                  <tr key={r.id} className="align-top text-slate-800 dark:text-slate-100">
                    <td className="px-4 py-3 whitespace-nowrap">{formatearFecha(r.created_at)}</td>
                    <td className="px-4 py-3">
                      <Etiqueta color="azul">{r.action}</Etiqueta>
                    </td>
                    <td className="px-4 py-3">
                      {RECURSOS[r.resource] ?? r.resource}
                      {r.resource_id && (
                        <span className="block font-mono text-xs text-slate-500 dark:text-slate-400">
                          {r.resource_id}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">
                      {r.actor_id}
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      <Detalles detalles={r.details} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}

function Detalles({ detalles = {} }) {
  const pares = Object.entries(detalles)
  if (pares.length === 0) return <span aria-label="Sin detalle">—</span>
  return (
    <ul className="space-y-0.5">
      {pares.map(([clave, valor]) => (
        <li key={clave}>
          <span className="font-medium text-slate-800 dark:text-slate-100">{clave}:</span>{' '}
          {typeof valor === 'object' ? JSON.stringify(valor) : String(valor)}
        </li>
      ))}
    </ul>
  )
}
