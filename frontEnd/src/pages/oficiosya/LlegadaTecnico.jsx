import { Clock, LocateFixed, Play } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { CircleMarker, Marker, Polyline, useMap } from 'react-leaflet'
import { Mapa } from '@/components/mapa/Mapa'
import { Boton } from '@/components/ui/Boton'
import { useModo } from '@/hooks/useModo'
import { useUbicacion } from '@/hooks/useUbicacion'
import { distanciaKm } from '@/utils/distancia'
import {
  CONDICIONES_VIA,
  FACTOR_RUTA,
  minutosDeLlegada,
  recorridoEn,
  velocidadEn,
} from '@/utils/ecuaciones'
import { coordenadasDeZona, NOMBRES_ZONAS } from '@/utils/zonas'

/** Duración real de la animación, sin importar cuántos minutos simule. */
const DURACION_ANIMACION_MS = 6000
const MI_UBICACION = 'Mi ubicación'
const num = (n, decimales = 0) =>
  n.toLocaleString('es-CO', { maximumFractionDigits: decimales, minimumFractionDigits: decimales })

/**
 * Tiempo estimado de llegada del técnico con la EDO dv/dt = (v_máx − v)/τ (utils/ecuaciones.js).
 * La distancia sale de Haversine entre el técnico y el destino; en Modo Emergencia la vía es
 * más lenta. El botón anima el recorrido x(t) sobre el mapa y la curva v(t).
 */
export function LlegadaTecnico({ tecnico }) {
  const { enEmergencia } = useModo()
  const gps = useUbicacion()
  const [destino, setDestino] = useState(() =>
    tecnico.zona === NOMBRES_ZONAS[0] ? NOMBRES_ZONAS[1] : NOMBRES_ZONAS[0],
  )
  const [miUbicacion, setMiUbicacion] = useState(null)
  const [simularEmergencia, setSimularEmergencia] = useState(null) // null = usar el modo real
  const [minuto, setMinuto] = useState(null) // minuto simulado durante la animación
  const animacion = useRef(null)

  const emergencia = simularEmergencia ?? enEmergencia
  const via = emergencia ? CONDICIONES_VIA.EMERGENCIA : CONDICIONES_VIA.COTIDIANO
  const origen = tecnico.coordenadas
  const fin = destino === MI_UBICACION && miUbicacion ? miUbicacion : coordenadasDeZona(destino)
  const lineaRecta = distanciaKm(origen, fin)
  const km = lineaRecta * FACTOR_RUTA
  const llegada = minutosDeLlegada(km, via)

  useEffect(() => () => cancelAnimationFrame(animacion.current), [])

  function detener() {
    cancelAnimationFrame(animacion.current)
    setMinuto(null)
  }

  function simular() {
    cancelAnimationFrame(animacion.current)
    const inicio = performance.now()
    const paso = (ahora) => {
      const fraccion = Math.min((ahora - inicio) / DURACION_ANIMACION_MS, 1)
      setMinuto(fraccion * llegada)
      if (fraccion < 1) animacion.current = requestAnimationFrame(paso)
    }
    animacion.current = requestAnimationFrame(paso)
  }

  // Posición en el mapa: la fracción recorrida x(t)/d sobre la línea técnico → destino.
  const t = minuto ?? 0
  const avance = km > 0 ? Math.min(recorridoEn(t, via) / km, 1) : 1
  const posicion = [
    origen[0] + (fin[0] - origen[0]) * avance,
    origen[1] + (fin[1] - origen[1]) * avance,
  ]

  return (
    <section
      className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-3 dark:bg-slate-900"
      aria-labelledby="titulo-llegada"
    >
      <h2
        id="titulo-llegada"
        className="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-white"
      >
        <Clock className="size-5" aria-hidden="true" />
        ¿Cuánto tarda en llegar?
      </h2>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
        Estimación con una ecuación diferencial: el técnico arranca quieto y va tomando la velocidad
        de la vía.
      </p>

      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="flex flex-wrap items-end gap-2">
            <label className="flex-1">
              <span className="text-sm font-medium text-slate-800 dark:text-slate-100">
                ¿A dónde debe ir?
              </span>
              <select
                value={destino}
                onChange={(e) => {
                  detener()
                  setDestino(e.target.value)
                }}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-white/20 dark:bg-slate-800 dark:text-white"
              >
                {miUbicacion && <option value={MI_UBICACION}>{MI_UBICACION}</option>}
                {NOMBRES_ZONAS.map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </label>
            <Boton
              type="button"
              variante="secundario"
              cargando={gps.buscando}
              onClick={() =>
                gps.pedir((coordenadas) => {
                  detener()
                  setMiUbicacion(coordenadas)
                  setDestino(MI_UBICACION)
                })
              }
            >
              {!gps.buscando && <LocateFixed className="size-4" aria-hidden="true" />}
              Usar mi ubicación
            </Boton>
          </div>
          {gps.error && <p className="text-sm text-alerta-700 dark:text-red-300">{gps.error}</p>}

          <label className="flex items-center gap-2 text-sm text-slate-800 dark:text-slate-100">
            <input
              type="checkbox"
              checked={emergencia}
              onChange={(e) => {
                detener()
                setSimularEmergencia(e.target.checked)
              }}
              className="size-4 accent-alerta-600"
            />
            Modo emergencia (lluvia, vías cerradas)
            {enEmergencia && (
              <span className="text-xs text-alerta-700 dark:text-red-300">
                · activo en la ciudad
              </span>
            )}
          </label>

          <div className="rounded-xl bg-slate-50 p-4 font-mono text-sm text-slate-800 dark:bg-white/5 dark:text-slate-100">
            <p>dv/dt = (v_máx − v)/τ &nbsp;·&nbsp; v(0) = 0</p>
            <p className="mt-1">
              v(t) = v_máx·(1 − e<sup>−t/τ</sup>)
            </p>
            <p className="mt-1">
              x(t) = v_máx·[t − τ(1 − e<sup>−t/τ</sup>)] = d
            </p>
            <p className="mt-2 font-sans text-xs text-slate-600 dark:text-slate-300">
              v_máx = {via.velocidadMax} km/h · τ = {via.arranqueMin} min · d = Haversine (
              {num(lineaRecta, 2)} km) × {num(FACTOR_RUTA, 1)} por las calles. El tiempo t se
              despeja con el método de bisección.
            </p>
          </div>

          <dl className="grid grid-cols-3 gap-3">
            <Dato nombre="Distancia" valor={`${num(km, 1)} km`} />
            <Dato
              nombre="Velocidad"
              valor={`${num(minuto === null ? via.velocidadMax : velocidadEn(t, via))} km/h`}
            />
            <Dato
              nombre={minuto === null ? 'Llega en' : 'Minuto'}
              valor={minuto === null ? `${num(llegada)} min` : `${num(t)} / ${num(llegada)}`}
            />
          </dl>

          <Boton type="button" onClick={simular} className="w-full">
            <Play className="size-4" aria-hidden="true" />
            {minuto === null ? 'Simular recorrido' : 'Repetir recorrido'}
          </Boton>

          <CurvaVelocidad via={via} llegada={llegada} minuto={minuto} />
        </div>

        <Mapa centro={origen} zoom={13} className="h-80 lg:h-full lg:min-h-96">
          <Encuadrar puntos={[origen, fin]} />
          <Marker position={origen} title={`Técnico: ${tecnico.full_name}`} />
          <Marker position={fin} title="Destino" />
          <Polyline
            positions={[origen, fin]}
            pathOptions={{ color: '#64748b', dashArray: '6 6' }}
          />
          <Polyline positions={[origen, posicion]} pathOptions={{ color: '#16a34a', weight: 5 }} />
          <CircleMarker
            center={posicion}
            radius={9}
            pathOptions={{ color: '#16a34a', fillColor: '#ffffff', fillOpacity: 1, weight: 4 }}
          />
        </Mapa>
      </div>
    </section>
  )
}

/** Ajusta el zoom del mapa para que se vean el técnico y el destino. */
function Encuadrar({ puntos }) {
  const mapa = useMap()
  const clave = JSON.stringify(puntos)
  useEffect(() => {
    mapa.fitBounds(JSON.parse(clave), { padding: [40, 40], maxZoom: 15 })
  }, [mapa, clave])
  return null
}

function Dato({ nombre, valor }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3 dark:bg-white/5">
      <dt className="text-xs text-slate-600 dark:text-slate-300">{nombre}</dt>
      <dd className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{valor}</dd>
    </div>
  )
}

/** Gráfica SVG de v(t) hasta la llegada, con un punto que avanza durante la animación. */
function CurvaVelocidad({ via, llegada, minuto }) {
  const ancho = 400
  const alto = 140
  const izq = 34
  const abajo = 20
  const total = Math.max(llegada, 1)
  const x = (t) => izq + (t / total) * (ancho - izq - 8)
  const y = (v) => alto - abajo - (v / via.velocidadMax) * (alto - abajo - 14)
  const pasos = 60
  const camino = Array.from({ length: pasos + 1 }, (_, i) => (i / pasos) * total)
    .map((t, i) => `${i ? 'L' : 'M'}${x(t).toFixed(1)} ${y(velocidadEn(t, via)).toFixed(1)}`)
    .join(' ')

  return (
    <figure>
      <svg
        viewBox={`0 0 ${ancho} ${alto}`}
        className="w-full"
        role="img"
        aria-label={`Velocidad del técnico: sube desde 0 hasta ${via.velocidadMax} km/h`}
      >
        <line
          x1={izq}
          x2={ancho - 8}
          y1={y(via.velocidadMax)}
          y2={y(via.velocidadMax)}
          strokeDasharray="5 4"
          className="stroke-amber-600 dark:stroke-amber-400"
        />
        <text
          x={ancho - 10}
          y={y(via.velocidadMax) - 4}
          textAnchor="end"
          className="fill-amber-700 text-[11px] dark:fill-amber-300"
        >
          v_máx {via.velocidadMax} km/h
        </text>
        <line
          x1={izq}
          x2={ancho - 8}
          y1={alto - abajo}
          y2={alto - abajo}
          className="stroke-slate-300 dark:stroke-white/20"
        />
        <text
          x={izq - 4}
          y={alto - abajo + 4}
          textAnchor="end"
          className="fill-slate-500 text-[11px]"
        >
          0
        </text>
        <text x={izq} y={alto - 4} className="fill-slate-500 text-[11px] dark:fill-slate-400">
          0 min
        </text>
        <text
          x={ancho - 8}
          y={alto - 4}
          textAnchor="end"
          className="fill-slate-500 text-[11px] dark:fill-slate-400"
        >
          {num(llegada)} min
        </text>
        <path d={camino} fill="none" strokeWidth="3" className="stroke-green-600" />
        {minuto !== null && (
          <circle
            cx={x(minuto)}
            cy={y(velocidadEn(minuto, via))}
            r="5"
            className="fill-green-600"
          />
        )}
      </svg>
      <figcaption className="text-xs text-slate-600 dark:text-slate-300">
        Velocidad v(t): sube rápido al inicio y se acerca a v_máx sin pasarla.
      </figcaption>
    </figure>
  )
}
