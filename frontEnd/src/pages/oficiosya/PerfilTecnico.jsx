import { useMutation, useQuery } from '@tanstack/react-query'
import { BadgeCheck, MapPin, MessageCircle } from 'lucide-react'
import { useRef } from 'react'
import { useParams } from 'react-router'
import { Circle } from 'react-leaflet'
import { enlaceWhatsapp, obtenerTecnico } from '@/api/oficiosya'
import { Mapa } from '@/components/mapa/Mapa'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Cargando, ErrorAlCargar } from '@/components/ui/Estados'
import { Estrellas } from '@/components/ui/Estrellas'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { Volver } from '@/components/ui/Volver'
import { Disponibilidad } from './Disponibilidad'

/** CU-19 paso 5: perfil del técnico, con contacto por WhatsApp (CU-22). */
export default function PerfilTecnico() {
  const { id } = useParams()
  const {
    data: t,
    isPending,
    error,
  } = useQuery({
    queryKey: ['tecnico', id],
    queryFn: () => obtenerTecnico(id),
  })

  return (
    <>
      <Volver a="/oficiosya">Volver a OficiosYa</Volver>
      <div className="mt-4">
        {isPending ? (
          <Cargando />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <section className="rounded-2xl bg-white p-6 shadow-sm">
                <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
                  {t.fullName}
                  <BadgeCheck className="size-6 text-marca-600" aria-label="Técnico verificado" />
                </h1>
                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <Estrellas valor={t.rating} total={t.totalReviews} />
                  <Disponibilidad disponible={t.disponible} />
                  <span className="text-sm text-slate-600">
                    {t.experienceYears} años de experiencia
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {t.specialties.map((e) => (
                    <Etiqueta key={e} color="azul">
                      {e}
                    </Etiqueta>
                  ))}
                </div>
                <p className="mt-4 text-slate-700">{t.bio}</p>
              </section>

              <section
                className="rounded-2xl bg-white p-6 shadow-sm"
                aria-labelledby="titulo-resenas"
              >
                <h2 id="titulo-resenas" className="font-semibold text-slate-900">
                  Reseñas
                </h2>
                {t.resenas.length === 0 ? (
                  <p className="mt-2 text-sm text-slate-600">Todavía no tiene reseñas.</p>
                ) : (
                  <ul className="mt-3 divide-y divide-slate-100">
                    {t.resenas.map((r) => (
                      <li key={r.id} className="py-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-slate-900">{r.authorName}</span>
                          <Estrellas valor={r.rating} />
                        </div>
                        <p className="mt-1 text-sm text-slate-700">{r.comment}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>

            <aside className="space-y-6">
              <ContactoWhatsapp tecnico={t} />
              <section>
                <h2 className="mb-2 flex items-center gap-1 font-semibold text-slate-900">
                  <MapPin className="size-4" aria-hidden="true" />
                  Trabaja en {t.zona}
                </h2>
                <Mapa centro={t.coordenadas} zoom={14} className="h-56">
                  <Circle center={t.coordenadas} radius={500} pathOptions={{ color: '#1d4ed8' }} />
                </Mapa>
              </section>
            </aside>
          </div>
        )}
      </div>
    </>
  )
}

/**
 * CU-22. Antes de abrir WhatsApp se informa qué se comparte y se pide autorización.
 * Sin autorización no se genera el enlace.
 */
function ContactoWhatsapp({ tecnico }) {
  const dialogo = useRef(null)
  // El enlace se muestra como botón tras autorizar: abrir la ventana sola después de esperar
  // al servidor lo bloquean algunos navegadores.
  const contacto = useMutation({ mutationFn: () => enlaceWhatsapp(tecnico) })

  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm">
      <h2 className="font-semibold text-slate-900">Contactar</h2>
      <p className="mt-1 text-sm text-slate-600">
        Habla directamente con {tecnico.fullName.split(' ')[0]}.
      </p>
      <Boton variante="exito" className="mt-4 w-full" onClick={() => dialogo.current.showModal()}>
        <MessageCircle className="size-4" aria-hidden="true" />
        Escribir por WhatsApp
      </Boton>

      <dialog
        ref={dialogo}
        aria-labelledby="titulo-autorizacion"
        className="m-auto w-[min(28rem,calc(100%-2rem))] rounded-2xl p-6 backdrop:bg-slate-900/50"
      >
        <h3 id="titulo-autorizacion" className="text-lg font-semibold text-slate-900">
          ¿Autorizas el contacto?
        </h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
          <li>Se abrirá WhatsApp con un mensaje de saludo. Tu número lo verá el técnico.</li>
          <li>PrevenRed solo guarda que hubo un contacto: tú, el técnico y la fecha.</li>
          <li>La conversación sigue fuera de la plataforma.</li>
        </ul>
        {contacto.error && (
          <div className="mt-3">
            <Alerta tipo="error">No se pudo abrir WhatsApp. Intenta de nuevo.</Alerta>
          </div>
        )}
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Boton variante="secundario" onClick={() => dialogo.current.close()}>
            {contacto.data ? 'Cerrar' : 'No, cancelar'}
          </Boton>
          {contacto.data ? (
            <a
              href={contacto.data}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => dialogo.current.close()}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 font-medium text-white hover:bg-green-700"
            >
              <MessageCircle className="size-4" aria-hidden="true" />
              Abrir WhatsApp
            </a>
          ) : (
            <Boton cargando={contacto.isPending} onClick={() => contacto.mutate()}>
              Sí, autorizo
            </Boton>
          )}
        </div>
      </dialog>
    </section>
  )
}
