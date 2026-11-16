import { useQuery } from '@tanstack/react-query'
import { Home, MapPin, Plus, Users } from 'lucide-react'
import { Link } from 'react-router'
import { HABITABILIDAD, listarInspecciones, NIVELES_DANO } from '@/api/inspecciones'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { useAuth } from '@/hooks/useAuth'
import { formatearFecha } from '@/utils/fechas'
import { esAdministrador } from '@/utils/roles'

const COLOR_HABITABILIDAD = { HABITABLE: 'verde', RESTRINGIDO: 'ambar', EVACUACION: 'gris' }

const COLOR_DANO = {
  LEVE: 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200',
  MODERADO: 'bg-amber-100 text-amber-900 dark:bg-amber-400/15 dark:text-amber-200',
  SEVERO: 'bg-orange-100 text-orange-800 dark:bg-orange-400/15 dark:text-orange-200',
  DESTRUIDO: 'bg-alerta-50 text-alerta-700 dark:bg-red-950/60 dark:text-red-200',
}

/**
 * CU-35 · Consultar censos e inspecciones de inmuebles.
 *  - Inspector: ve las inspecciones que él registró.
 *  - Administrador: ve las más recientes de todos los evaluadores.
 */
export default function Inspecciones() {
  const { usuario } = useAuth()
  const admin = esAdministrador(usuario?.role)
  const {
    data: inspecciones = [],
    isPending,
    error,
  } = useQuery({ queryKey: ['inspecciones'], queryFn: listarInspecciones })

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Censo e inspecciones
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-300">
            {admin
              ? 'Inspecciones de habitabilidad registradas por todos los evaluadores de campo.'
              : 'Las inspecciones de habitabilidad que has registrado.'}
          </p>
        </div>
        <Link
          to="/inspecciones/nueva"
          className="inline-flex items-center gap-2 rounded-lg bg-marca-600 px-4 py-2.5 font-medium text-white hover:bg-marca-700 dark:bg-amber-500 dark:text-slate-950 dark:hover:bg-amber-400"
        >
          <Plus className="size-4" aria-hidden="true" />
          Nueva inspección
        </Link>
      </div>

      <div className="mt-5">
        {isPending ? (
          <Cargando texto="Cargando inspecciones…" />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : inspecciones.length === 0 ? (
          <SinResultados titulo="Aún no hay inspecciones">
            Registra la primera inspección de un inmueble afectado.
          </SinResultados>
        ) : (
          <>
            <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
              {inspecciones.length === 1 ? '1 inspección' : `${inspecciones.length} inspecciones`} ·
              más recientes primero
            </p>
            <ul className="space-y-3">
              {inspecciones.map((i) => (
                <li key={i.id}>
                  <TarjetaInspeccion inspeccion={i} />
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </>
  )
}

function TarjetaInspeccion({ inspeccion: i }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-white">
            <Home className="size-4 text-marca-600 dark:text-amber-400" aria-hidden="true" />
            {i.property_address}
          </h2>
          <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">{i.neighborhood}</p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${COLOR_DANO[i.damage_level] ?? COLOR_DANO.LEVE}`}
          >
            Daño {NIVELES_DANO[i.damage_level]?.toLowerCase() ?? i.damage_level}
          </span>
          <Etiqueta color={COLOR_HABITABILIDAD[i.habitability] ?? 'gris'}>
            {HABITABILIDAD[i.habitability] ?? i.habitability}
          </Etiqueta>
        </div>
      </div>
      {i.technical_notes && (
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">{i.technical_notes}</p>
      )}
      <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
        <span className="inline-flex items-center gap-1">
          <Users className="size-3.5" aria-hidden="true" />
          {i.residents_count === 1 ? '1 residente' : `${i.residents_count} residentes`}
        </span>
        <span>Inspeccionado: {formatearFecha(i.created_at)}</span>
        <a
          href={`https://www.openstreetmap.org/?mlat=${i.latitude}&mlon=${i.longitude}#map=17/${i.latitude}/${i.longitude}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 font-medium text-marca-700 hover:underline dark:text-amber-400"
        >
          <MapPin className="size-3.5" aria-hidden="true" />
          Ver ubicación
        </a>
      </p>
    </article>
  )
}
