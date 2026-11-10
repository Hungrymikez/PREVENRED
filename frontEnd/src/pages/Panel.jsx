import { ArrowRight, ClipboardList, MapPin, Siren } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import fotoDia from '@/assets/pereira-dia.webp'
import fotoNoche from '@/assets/viaducto-pereira-noche.webp'
import { useAuth } from '@/hooks/useAuth'
import { useModo } from '@/hooks/useModo'
import { useTema } from '@/hooks/useTema'
import { AccionesEmergencia } from '@/pages/emergencia/AccionesEmergencia'
import { MODULOS } from '@/utils/modulos'

/** Color propio de cada módulo (clases completas para que Tailwind las incluya). */
const TONOS = {
  verde: {
    icono: 'bg-emerald-100 dark:bg-emerald-400/15 text-emerald-700 dark:text-emerald-300',
    borde: 'hover:border-emerald-500',
    flecha: 'text-emerald-600 dark:text-emerald-400',
  },
  naranja: {
    icono: 'bg-orange-100 dark:bg-orange-400/15 text-orange-700 dark:text-orange-300',
    borde: 'hover:border-orange-500',
    flecha: 'text-orange-600 dark:text-orange-400',
  },
  rosa: {
    icono: 'bg-rose-100 dark:bg-rose-400/15 text-rose-700 dark:text-rose-300',
    borde: 'hover:border-rose-500',
    flecha: 'text-rose-600 dark:text-rose-400',
  },
  gris: {
    icono: 'bg-slate-100 dark:bg-white/10 text-slate-700 dark:text-slate-200',
    borde: 'hover:border-slate-500',
    flecha: 'text-slate-600 dark:text-slate-300',
  },
}

const fechaDeHoy = new Intl.DateTimeFormat('es-CO', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

/**
 * Página de inicio con sesión: portada con una foto de Pereira (de día o de noche según
 * el tema elegido en el login), el saludo y los módulos, cada uno con su color.
 * En Modo Emergencia lo primero son los reportes; los módulos del día a día quedan debajo.
 */
export default function Panel() {
  const { usuario } = useAuth()
  const { enEmergencia } = useModo()
  const { oscuro } = useTema()
  const nombre = usuario.full_name.split(' ')[0]
  const modulos = MODULOS.filter((m) => m.descripcion)
  const [hoy] = useState(() => fechaDeHoy.format(new Date()))

  return (
    <>
      <section
        aria-labelledby="saludo"
        className="relative isolate overflow-hidden rounded-3xl bg-slate-900 shadow-sm"
      >
        <img
          src={oscuro ? fotoNoche : fotoDia}
          alt=""
          aria-hidden="true"
          className={`absolute inset-0 -z-10 size-full object-cover ${oscuro ? 'object-center' : 'object-[center_35%]'}`}
        />
        <div
          aria-hidden="true"
          className={`absolute inset-0 -z-10 bg-linear-to-r ${
            enEmergencia
              ? 'from-alerta-700/90 via-alerta-700/60 to-alerta-700/20'
              : 'from-slate-950/80 via-slate-950/45 to-slate-950/5'
          }`}
        />
        <div className="px-5 py-8 text-white sm:px-8 sm:py-12">
          <p className="text-sm font-medium text-white/80 first-letter:uppercase">{hoy}</p>
          <h1 id="saludo" className="mt-1 text-3xl font-bold sm:text-4xl">
            Hola, {nombre}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 backdrop-blur-sm">
              <MapPin className="size-4" aria-hidden="true" />
              {usuario.neighborhood}
            </span>
            {enEmergencia ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 font-semibold text-alerta-700 dark:bg-slate-900 dark:text-red-300">
                <Siren className="size-4" aria-hidden="true" />
                Modo Emergencia
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 backdrop-blur-sm">
                <span className="size-2 rounded-full bg-emerald-400" aria-hidden="true" />
                Modo cotidiano
              </span>
            )}
          </div>
          <p className="mt-4 max-w-md text-white/90">
            {enEmergencia
              ? 'Reporta daños o pide ayuda en 3 pasos. Tu reporte llega a los equipos de atención.'
              : `¿Qué quieres hacer hoy en ${usuario.neighborhood}?`}
          </p>
        </div>
      </section>

      {enEmergencia && (
        <section className="mt-6" aria-labelledby="titulo-emergencia">
          <h2
            id="titulo-emergencia"
            className="mb-3 text-lg font-semibold text-alerta-700 dark:text-red-300"
          >
            ¿Necesitas reportar algo?
          </h2>
          <AccionesEmergencia />
        </section>
      )}

      <section className="mt-8" aria-labelledby="titulo-modulos">
        <h2
          id="titulo-modulos"
          className="mb-3 text-lg font-semibold text-slate-900 dark:text-white"
        >
          {enEmergencia ? 'Otros servicios' : 'Servicios para tu barrio'}
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {modulos.map((modulo) => (
            <li key={modulo.ruta}>
              <TarjetaModulo {...modulo} />
            </li>
          ))}
          <li>
            <TarjetaModulo
              ruta="/emergencia/casos"
              nombre="Mis casos"
              descripcion="Sigue el estado de los reportes que has hecho."
              Icono={ClipboardList}
              tono="gris"
            />
          </li>
        </ul>
      </section>
    </>
  )
}

function TarjetaModulo({ ruta, nombre, descripcion, Icono, tono }) {
  const colores = TONOS[tono] ?? TONOS.gris
  return (
    <Link
      to={ruta}
      className={`group flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md focus-visible:ring-2 focus-visible:ring-marca-600 focus-visible:outline-none dark:border-white/10 dark:bg-slate-900 dark:focus-visible:ring-amber-400 ${colores.borde}`}
    >
      <span className={`flex size-12 items-center justify-center rounded-xl ${colores.icono}`}>
        <Icono className="size-6" aria-hidden="true" />
      </span>
      <h3 className="mt-4 font-semibold text-slate-900 dark:text-white">{nombre}</h3>
      <p className="mt-1 flex-1 text-sm text-slate-600 dark:text-slate-300">{descripcion}</p>
      <span
        className={`mt-4 inline-flex items-center gap-1 text-sm font-medium ${colores.flecha}`}
        aria-hidden="true"
      >
        Entrar
        <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
      </span>
    </Link>
  )
}
