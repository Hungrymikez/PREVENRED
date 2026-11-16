import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Shuffle } from 'lucide-react'
import { useState } from 'react'
import { mensajeDeError } from '@/api/client'
import {
  CATEGORIAS_AYUDA,
  ejecutarEmparejamiento,
  formatearCantidad,
  listarNecesidadesPendientes,
  listarOfertasPendientes,
  PRIORIDADES,
} from '@/api/donaciones'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'

const COLOR_PRIORIDAD = {
  BAJA: 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200',
  MEDIA: 'bg-amber-100 text-amber-900 dark:bg-amber-400/15 dark:text-amber-200',
  ALTA: 'bg-orange-100 text-orange-800 dark:bg-orange-400/15 dark:text-orange-200',
  URGENTE: 'bg-alerta-50 text-alerta-700 dark:bg-red-950/60 dark:text-red-200',
}

/** Lo que falta (necesidad) o lo que queda (oferta); los datos antiguos no traen el campo. */
const restante = (item, campo) => item[campo] ?? item.quantity

/**
 * CU-41 Gestionar inventario de ayudas · CU-42 Emparejar donaciones (administrador).
 * Muestra necesidades sin cubrir y ofertas disponibles, y ejecuta el emparejamiento:
 * misma categoría y unidad, máximo a 15 km, primero las necesidades más urgentes.
 */
export default function GestionDonaciones() {
  const queryClient = useQueryClient()
  const necesidades = useQuery({
    queryKey: ['donaciones', 'necesidades'],
    queryFn: listarNecesidadesPendientes,
  })
  const ofertas = useQuery({
    queryKey: ['donaciones', 'ofertas'],
    queryFn: listarOfertasPendientes,
  })
  // Nombres de necesidades y ofertas en el momento de emparejar (luego pueden salir de la lista).
  const [resultado, setResultado] = useState(null)

  const emparejamiento = useMutation({
    mutationFn: ejecutarEmparejamiento,
    onSuccess: (matches) => {
      setResultado({
        matches,
        necesidades: Object.fromEntries((necesidades.data ?? []).map((n) => [n.id, n])),
        ofertas: Object.fromEntries((ofertas.data ?? []).map((o) => [o.id, o])),
      })
      queryClient.invalidateQueries({ queryKey: ['donaciones'] })
    },
  })

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Gestión de donaciones
          </h1>
          <p className="mt-1 max-w-2xl text-slate-600 dark:text-slate-300">
            Empareja las donaciones disponibles con las necesidades de la comunidad: misma categoría
            y unidad, a 15 km como máximo, empezando por las más urgentes.
          </p>
        </div>
        <Boton
          type="button"
          cargando={emparejamiento.isPending}
          onClick={() => emparejamiento.mutate()}
        >
          <Shuffle className="size-4" aria-hidden="true" />
          Ejecutar emparejamiento
        </Boton>
      </div>

      <div className="mt-4 space-y-3">
        {emparejamiento.error && (
          <Alerta tipo="error">{mensajeDeError(emparejamiento.error)}</Alerta>
        )}
        {resultado && <ResultadoEmparejamiento resultado={resultado} />}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Seccion
          titulo="Necesidades pendientes"
          consulta={necesidades}
          vacio="No hay necesidades sin cubrir."
        >
          {(n) => (
            <Item
              titulo={n.title}
              detalle={`${CATEGORIAS_AYUDA[n.category] ?? n.category} · Faltan ${formatearCantidad(restante(n, 'remaining_quantity'), n.unit)}`}
              extra={
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${COLOR_PRIORIDAD[n.priority] ?? COLOR_PRIORIDAD.BAJA}`}
                >
                  {PRIORIDADES[n.priority] ?? n.priority}
                </span>
              }
            />
          )}
        </Seccion>
        <Seccion
          titulo="Donaciones disponibles"
          consulta={ofertas}
          vacio="No hay donaciones disponibles."
        >
          {(o) => (
            <Item
              titulo={o.title}
              detalle={`${CATEGORIAS_AYUDA[o.category] ?? o.category} · Quedan ${formatearCantidad(restante(o, 'available_quantity'), o.unit)}`}
              extra={<Etiqueta color="verde">Disponible</Etiqueta>}
            />
          )}
        </Seccion>
      </div>
    </>
  )
}

function ResultadoEmparejamiento({ resultado }) {
  const { matches, necesidades, ofertas } = resultado
  if (matches.length === 0) {
    return (
      <Alerta tipo="info">
        No se encontraron coincidencias: revisa que categoría y unidad coincidan y que estén a menos
        de 15 km.
      </Alerta>
    )
  }
  return (
    <section
      aria-label="Emparejamientos creados"
      className="rounded-2xl border border-green-200 bg-white p-4 shadow-sm dark:border-green-400/30 dark:bg-slate-900"
    >
      <Alerta tipo="exito">
        {matches.length === 1
          ? 'Se creó 1 emparejamiento.'
          : `Se crearon ${matches.length} emparejamientos.`}
      </Alerta>
      <ul className="mt-3 divide-y divide-slate-200 dark:divide-white/10">
        {matches.map((m) => {
          const necesidad = necesidades[m.need_id]
          const oferta = ofertas[m.offer_id]
          const unidad = necesidad?.unit ?? oferta?.unit ?? ''
          return (
            <li key={m.id} className="flex flex-wrap items-center gap-2 py-2 text-sm">
              <span className="font-medium text-slate-900 dark:text-white">
                {oferta?.title ?? 'Donación'}
              </span>
              <ArrowRight className="size-4 text-slate-400" aria-hidden="true" />
              <span className="font-medium text-slate-900 dark:text-white">
                {necesidad?.title ?? 'Necesidad'}
              </span>
              <span className="text-slate-600 dark:text-slate-300">
                · {formatearCantidad(m.matched_quantity, unidad)} · a{' '}
                {(m.distance_meters / 1000).toLocaleString('es-CO', { maximumFractionDigits: 1 })}{' '}
                km
              </span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function Seccion({ titulo, consulta, vacio, children }) {
  const lista = consulta.data ?? []
  return (
    <section aria-label={titulo}>
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
        {titulo}
        {!consulta.isPending && !consulta.error && (
          <span className="ml-2 text-sm font-normal text-slate-500 dark:text-slate-400">
            ({lista.length})
          </span>
        )}
      </h2>
      <div className="mt-3">
        {consulta.isPending ? (
          <Cargando />
        ) : consulta.error ? (
          <ErrorAlCargar error={consulta.error} />
        ) : lista.length === 0 ? (
          <SinResultados titulo={vacio} />
        ) : (
          <ul className="space-y-2">
            {lista.map((item) => (
              <li key={item.id}>{children(item)}</li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

function Item({ titulo, detalle, extra }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 dark:border-white/10 dark:bg-slate-900">
      <div>
        <p className="font-medium text-slate-900 dark:text-white">{titulo}</p>
        <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">{detalle}</p>
      </div>
      {extra}
    </div>
  )
}
