import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ClipboardCheck, MapPin, UserRound } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import {
  asignarCaso,
  cambiarEstadoCaso,
  ESTADOS_CASO,
  GRAVEDADES,
  listarCasos,
  listarInspectores,
  TIPOS_CASO,
} from '@/api/casos'
import { mensajeDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Cargando, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { useAuth } from '@/hooks/useAuth'
import { formatearFecha } from '@/utils/fechas'
import { esAdministrador } from '@/utils/roles'

const COLOR_ESTADO = {
  REPORTADO: 'ambar',
  EN_REVISION: 'azul',
  ASIGNADO: 'azul',
  EN_ATENCION: 'azul',
  RESUELTO: 'verde',
}

const COLOR_GRAVEDAD = {
  BAJA: 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200',
  MEDIA: 'bg-amber-100 text-amber-900 dark:bg-amber-400/15 dark:text-amber-200',
  ALTA: 'bg-orange-100 text-orange-800 dark:bg-orange-400/15 dark:text-orange-200',
  CRITICA: 'bg-alerta-50 text-alerta-700 dark:bg-red-950/60 dark:text-red-200',
}

const CHIP =
  'rounded-full border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100 aria-pressed:border-marca-600 aria-pressed:bg-marca-600 aria-pressed:text-white dark:border-white/20 dark:text-slate-200 dark:hover:bg-white/10 dark:aria-pressed:border-amber-500 dark:aria-pressed:bg-amber-500 dark:aria-pressed:text-slate-950'

/**
 * CU-39 · Gestionar incidentes. Bandeja del personal de atención:
 *  - Administrador: ve todos los casos, los asigna a un Inspector y cambia el estado de cualquiera.
 *  - Inspector: ve primero los casos asignados a él y solo cambia el estado de esos.
 * El ciudadano no llega aquí: ve solo los suyos en "Mis casos" (ruta protegida por rol).
 */
export default function BandejaCasos() {
  const { usuario } = useAuth()
  const admin = esAdministrador(usuario.role)
  const [estado, setEstado] = useState('')
  const [soloMios, setSoloMios] = useState(!admin)

  const {
    data: casos = [],
    isPending,
    error,
  } = useQuery({
    queryKey: ['casos', estado, soloMios],
    queryFn: () => listarCasos({ estado, asignadosAMi: soloMios }),
  })
  // Solo el Administrador consulta la lista de inspectores (nombres y asignación).
  const { data: inspectores = [] } = useQuery({
    queryKey: ['inspectores'],
    queryFn: listarInspectores,
    enabled: admin,
  })

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Casos reportados</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        {admin
          ? 'Todos los reportes de la comunidad. Asigna cada caso a un inspector y sigue su avance.'
          : 'Atiende los casos que te asignaron y actualiza su estado.'}
      </p>

      {!admin && (
        <div className="mt-5 flex flex-wrap gap-2" role="group" aria-label="Qué casos ver">
          <button
            type="button"
            aria-pressed={soloMios}
            onClick={() => setSoloMios(true)}
            className={CHIP}
          >
            Asignados a mí
          </button>
          <button
            type="button"
            aria-pressed={!soloMios}
            onClick={() => setSoloMios(false)}
            className={CHIP}
          >
            Todos los casos
          </button>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Filtrar por estado">
        {[['', 'Todos los estados'], ...Object.entries(ESTADOS_CASO)].map(([valor, nombre]) => (
          <button
            key={valor || 'todos'}
            type="button"
            aria-pressed={estado === valor}
            onClick={() => setEstado(valor)}
            className={CHIP}
          >
            {nombre}
          </button>
        ))}
      </div>

      <div className="mt-5">
        {isPending ? (
          <Cargando texto="Cargando casos…" />
        ) : error ? (
          <Alerta tipo="error">{mensajeDeError(error)}</Alerta>
        ) : casos.length === 0 ? (
          <SinResultados titulo="No hay casos">
            {soloMios
              ? 'No tienes casos asignados con este filtro.'
              : estado
                ? `No hay casos en estado «${ESTADOS_CASO[estado]}».`
                : 'Cuando la comunidad reporte, los casos aparecerán aquí.'}
          </SinResultados>
        ) : (
          <>
            <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
              {casos.length === 1 ? '1 caso' : `${casos.length} casos`} · más recientes primero
            </p>
            <ul className="space-y-3">
              {casos.map((caso) => (
                <li key={caso.id}>
                  <TarjetaCaso
                    caso={caso}
                    admin={admin}
                    miId={usuario.id}
                    inspectores={inspectores}
                  />
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </>
  )
}

/** Texto del responsable según quién mira la bandeja. */
function nombreResponsable(caso, { admin, miId, inspectores }) {
  if (!caso.assigned_to) return 'Sin asignar'
  if (caso.assigned_to === miId) return 'Asignado a ti'
  if (admin) {
    const inspector = inspectores.find((i) => i.id === caso.assigned_to)
    return inspector ? `Asignado a ${inspector.full_name}` : 'Asignado'
  }
  return 'Asignado a otro inspector'
}

function TarjetaCaso({ caso, admin, miId, inspectores }) {
  const [accion, setAccion] = useState(null) // 'estado' | 'asignar' | null
  const puedeCambiarEstado = admin || caso.assigned_to === miId
  const puedeAsignar = admin && caso.status !== 'RESUELTO'
  const sinAsignar = !caso.assigned_to

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-sm font-semibold text-slate-900 dark:text-white">
            {caso.case_number}
          </p>
          <h2 className="mt-0.5 font-semibold text-slate-900 dark:text-white">
            {TIPOS_CASO[caso.incident_type] ?? caso.incident_type}
          </h2>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${COLOR_GRAVEDAD[caso.severity] ?? COLOR_GRAVEDAD.BAJA}`}
          >
            Gravedad {GRAVEDADES[caso.severity]?.toLowerCase() ?? caso.severity}
          </span>
          <Etiqueta color={COLOR_ESTADO[caso.status] ?? 'gris'}>
            {ESTADOS_CASO[caso.status] ?? caso.status}
          </Etiqueta>
        </div>
      </div>

      <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">{caso.description}</p>
      <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
        <span
          className={`inline-flex items-center gap-1 font-medium ${
            sinAsignar ? 'text-alerta-700 dark:text-red-300' : 'text-slate-700 dark:text-slate-200'
          }`}
        >
          <UserRound className="size-3.5" aria-hidden="true" />
          {nombreResponsable(caso, { admin, miId, inspectores })}
        </span>
        <span>Reportado: {formatearFecha(caso.created_at)}</span>
        <a
          href={`https://www.openstreetmap.org/?mlat=${caso.latitude}&mlon=${caso.longitude}#map=17/${caso.latitude}/${caso.longitude}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 font-medium text-marca-700 hover:underline dark:text-amber-400"
        >
          <MapPin className="size-3.5" aria-hidden="true" />
          Ver ubicación
        </a>
      </p>

      {accion === 'estado' && <CambioEstado caso={caso} onTerminar={() => setAccion(null)} />}
      {accion === 'asignar' && (
        <Asignacion caso={caso} inspectores={inspectores} onTerminar={() => setAccion(null)} />
      )}
      {accion === null && (
        <div className="mt-3 flex flex-wrap gap-2">
          {puedeAsignar && (
            <Boton
              type="button"
              variante={sinAsignar ? 'primario' : 'secundario'}
              onClick={() => setAccion('asignar')}
            >
              {sinAsignar ? 'Asignar inspector' : 'Reasignar'}
            </Boton>
          )}
          {puedeCambiarEstado && (
            <Boton type="button" variante="secundario" onClick={() => setAccion('estado')}>
              Cambiar estado
            </Boton>
          )}
          {puedeCambiarEstado && (
            <Link
              to={`/inspecciones/nueva?caso=${caso.id}&lat=${caso.latitude}&lon=${caso.longitude}`}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-sm font-medium text-marca-700 hover:bg-marca-50 dark:text-amber-400 dark:hover:bg-amber-400/10"
            >
              <ClipboardCheck className="size-4" aria-hidden="true" />
              Registrar inspección
            </Link>
          )}
        </div>
      )}
    </article>
  )
}

/** CU-39: el Administrador elige el inspector responsable del caso. */
function Asignacion({ caso, inspectores, onTerminar }) {
  const queryClient = useQueryClient()
  const opciones = inspectores.filter((i) => i.id !== caso.assigned_to)
  const [inspectorId, setInspectorId] = useState(opciones[0]?.id ?? '')
  const [notas, setNotas] = useState('')

  const asignacion = useMutation({
    mutationFn: () => asignarCaso(caso.id, { inspectorId, notas: notas.trim() }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['casos'] })
      onTerminar()
    },
  })

  if (opciones.length === 0) {
    return (
      <div className="mt-3 space-y-2">
        <Alerta tipo="info">No hay otros inspectores activos para asignar este caso.</Alerta>
        <Boton type="button" variante="secundario" onClick={onTerminar}>
          Cerrar
        </Boton>
      </div>
    )
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        asignacion.mutate()
      }}
      className="mt-3 space-y-3 rounded-xl bg-slate-50 p-3 dark:bg-white/5"
    >
      {asignacion.error && <Alerta tipo="error">{mensajeDeError(asignacion.error)}</Alerta>}
      <div className="grid gap-3 sm:grid-cols-2">
        <Campo
          como="select"
          etiqueta="Inspector responsable"
          value={inspectorId}
          onChange={(e) => setInspectorId(e.target.value)}
        >
          {opciones.map((i) => (
            <option key={i.id} value={i.id}>
              {i.full_name}
            </option>
          ))}
        </Campo>
        <Campo
          etiqueta="Indicaciones (opcional)"
          placeholder="Ej.: Prioridad alta, hay familias afectadas"
          maxLength={500}
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Boton type="submit" cargando={asignacion.isPending}>
          Asignar
        </Boton>
        <Boton type="button" variante="secundario" onClick={onTerminar}>
          Cancelar
        </Boton>
      </div>
    </form>
  )
}

function CambioEstado({ caso, onTerminar }) {
  const queryClient = useQueryClient()
  const opciones = Object.entries(ESTADOS_CASO).filter(([valor]) => valor !== caso.status)
  const [estado, setEstado] = useState(opciones[0][0])
  const [notas, setNotas] = useState('')

  const cambio = useMutation({
    mutationFn: () => cambiarEstadoCaso(caso.id, { estado, notas: notas.trim() }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['casos'] })
      onTerminar()
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        cambio.mutate()
      }}
      className="mt-3 space-y-3 rounded-xl bg-slate-50 p-3 dark:bg-white/5"
    >
      {cambio.error && <Alerta tipo="error">{mensajeDeError(cambio.error)}</Alerta>}
      <div className="grid gap-3 sm:grid-cols-2">
        <Campo
          como="select"
          etiqueta="Nuevo estado"
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
        >
          {opciones.map(([valor, nombre]) => (
            <option key={valor} value={valor}>
              {nombre}
            </option>
          ))}
        </Campo>
        <Campo
          etiqueta="Nota (opcional)"
          placeholder="Ej.: Brigada en sitio"
          maxLength={500}
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Boton type="submit" cargando={cambio.isPending}>
          Guardar
        </Boton>
        <Boton type="button" variante="secundario" onClick={onTerminar}>
          Cancelar
        </Boton>
      </div>
    </form>
  )
}
