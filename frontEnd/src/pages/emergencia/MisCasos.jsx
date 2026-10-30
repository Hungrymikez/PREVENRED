import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Search } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { CATEGORIAS_REPORTE, listarMisCasos, nombreTipo } from '@/api/incidentes'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { formatearFecha } from '@/utils/fechas'
import { EstadoCaso } from './EstadoCaso'
import { Pendientes } from './Pendientes'

/** CU-32 · Consultar el estado de mis casos. */
export default function MisCasos() {
  const navegar = useNavigate()
  const [numero, setNumero] = useState('')
  const {
    data: casos,
    isPending,
    error,
  } = useQuery({
    queryKey: ['mis-casos'],
    queryFn: listarMisCasos,
    networkMode: 'offlineFirst', // sin señal intenta igual y muestra el error en vez de quedarse cargando
  })

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900">Mis casos</h1>
      <p className="mt-1 text-slate-600">El estado de tus reportes y solicitudes de ayuda.</p>

      {/* A1: buscar por número de caso */}
      <form
        className="mt-5 flex items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (numero.trim()) navegar(`/emergencia/casos/${numero.trim().toUpperCase()}`)
        }}
      >
        <Campo
          etiqueta="Buscar por número de caso"
          placeholder="PR-2026-00041"
          value={numero}
          onChange={(e) => setNumero(e.target.value)}
          className="flex-1"
        />
        <Boton type="submit" variante="secundario" aria-label="Buscar caso">
          <Search className="size-4" aria-hidden="true" />
        </Boton>
      </form>

      <Pendientes />

      <div className="mt-6">
        {isPending ? (
          <Cargando />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : casos.length === 0 ? (
          <SinResultados titulo="Aún no tienes casos">
            Cuando hagas un reporte o pidas ayuda, aparecerá aquí.
          </SinResultados>
        ) : (
          <ul className="divide-y divide-slate-100 rounded-2xl bg-white shadow-sm">
            {casos.map((caso) => (
              <li key={caso.caseId}>
                <Link
                  to={`/emergencia/casos/${caso.caseId}`}
                  className="flex items-center gap-3 p-4 hover:bg-slate-50"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-sm font-semibold text-slate-900">{caso.caseId}</p>
                    <p className="text-slate-700">
                      {CATEGORIAS_REPORTE[caso.categoria].titulo} · {nombreTipo(caso)}
                    </p>
                    <p className="text-xs text-slate-500">{formatearFecha(caso.reportedAt)}</p>
                  </div>
                  <EstadoCaso caso={caso} />
                  <ChevronRight className="size-5 text-slate-400" aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}
