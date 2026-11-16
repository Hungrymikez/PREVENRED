import { ShieldCheck } from 'lucide-react'
import { Link, Outlet, useLocation } from 'react-router'
import fotoDia from '@/assets/pereira-dia.webp'
import fotoNoche from '@/assets/viaducto-pereira-noche.webp'
import { InterruptorTema } from '@/components/InterruptorTema'
import { useTema } from '@/hooks/useTema'

const FONDOS = {
  claro: {
    foto: fotoDia,
    credito: 'Centro de Pereira, Risaralda',
    encuadre: 'object-[center_40%]',
  },
  oscuro: {
    foto: fotoNoche,
    credito: 'Viaducto César Gaviria Trujillo · Pereira, Risaralda',
    encuadre: 'object-center',
  },
}

/**
 * Marco de las páginas de login y registro: foto de Pereira de fondo (de día en el
 * tema claro, de noche en el oscuro), un mensaje de bienvenida a la izquierda y la
 * tarjeta del formulario a la derecha. En celular el mensaje va arriba, más corto.
 */
export function LayoutAuth() {
  const { pathname } = useLocation()
  const { tema, oscuro, alternar } = useTema()
  const ancho = pathname.startsWith('/registro') ? 'max-w-md' : 'max-w-sm'
  const fondo = FONDOS[tema]

  return (
    <main data-tema={tema} className="relative isolate min-h-screen px-4 py-16 sm:px-8">
      <img
        key={tema}
        src={fondo.foto}
        alt=""
        aria-hidden="true"
        className={`fixed inset-0 -z-10 size-full object-cover ${fondo.encuadre}`}
      />
      {/* Oscurece el lado del texto para que se lea; el lado del formulario deja ver la foto. */}
      <div
        aria-hidden="true"
        className="fixed inset-0 -z-10 bg-linear-to-b from-slate-950/70 via-slate-950/35 to-slate-950/20 lg:bg-linear-to-r lg:from-slate-950/75 lg:via-slate-950/35 lg:to-slate-950/10 dark:from-slate-950/80 dark:lg:from-slate-950/85"
      />

      <div className="absolute top-4 right-4">
        <InterruptorTema oscuro={oscuro} onAlternar={alternar} />
      </div>

      <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-6xl flex-col items-center justify-center gap-8 lg:flex-row lg:justify-between lg:gap-16">
        <section className="max-w-xl text-white [text-shadow:0_1px_4px_rgb(0_0_0/0.5)] lg:flex-1">
          <Link to="/" className="inline-flex items-center gap-2 text-xl font-bold">
            <ShieldCheck className="size-7 text-white dark:text-amber-400" aria-hidden="true" />
            PrevenRed
          </Link>
          <p className="mt-4 text-3xl leading-tight font-bold text-balance sm:text-4xl lg:mt-8 lg:text-5xl">
            Pereira más preparada, entre vecinos
          </p>
          <p className="mt-3 text-base text-white/90 sm:text-lg lg:mt-5 lg:text-xl">
            Materiales, técnicos, bienestar y reportes de emergencia en un solo lugar.
          </p>
        </section>

        <div
          className={`w-full ${ancho} shrink-0 rounded-2xl bg-white/95 p-6 shadow-2xl ring-1 ring-black/5 backdrop-blur-md sm:p-7 dark:bg-slate-950/65 dark:text-white dark:ring-white/15`}
        >
          <Outlet />
        </div>
      </div>

      <p className="absolute bottom-4 left-4 text-xs font-medium text-white/85 [text-shadow:0_1px_3px_rgb(0_0_0/0.8)] sm:left-8">
        {fondo.credito}
      </p>
    </main>
  )
}
