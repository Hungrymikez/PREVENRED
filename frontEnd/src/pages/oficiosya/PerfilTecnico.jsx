import { useMutation, useQuery } from '@tanstack/react-query'
import { BadgeCheck, MapPin, MessageCircle } from 'lucide-react'
import { useRef } from 'react'
import { useParams } from 'react-router'
import { Circle } from 'react-leaflet'
import { mensajeDeError } from '@/api/client'
import { enlaceWhatsapp, nombreEspecialidad, obtenerTecnico } from '@/api/oficiosya'
import { Mapa } from '@/components/mapa/Mapa'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Cargando } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { Volver } from '@/components/ui/Volver'
import { Valoracion } from './Valoracion'

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
          <Alerta tipo="error">{mensajeDeError(error)}</Alerta>
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            <section className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2 dark:bg-slate-900">
              <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900 dark:text-white">
                {t.full_name}
                {t.verification_status === 'VERIFICADO' && (
                  <BadgeCheck
                    className="size-6 text-marca-600 dark:text-amber-400"
                    aria-label="Técnico verificado"
                  />
                )}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                <Valoracion tecnico={t} />
                <span className="text-sm text-slate-600 dark:text-slate-300">
                  {t.experience_years === 1
                    ? '1 año de experiencia'
                    : `${t.experience_years} años de experiencia`}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {t.specialties.map((e) => (
                  <Etiqueta key={e} color="azul">
                    {nombreEspecialidad(e)}
                  </Etiqueta>
                ))}
              </div>
              {t.bio && <p className="mt-4 text-slate-700 dark:text-slate-200">{t.bio}</p>}
            </section>

            <aside className="space-y-6">
              <ContactoWhatsapp tecnico={t} />
              <section>
                <h2 className="mb-2 flex items-center gap-1 font-semibold text-slate-900 dark:text-white">
                  <MapPin className="size-4" aria-hidden="true" />
                  Trabaja cerca de {t.zona}
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
    <section className="rounded-2xl bg-white p-6 shadow-sm dark:bg-slate-900">
      <h2 className="font-semibold text-slate-900 dark:text-white">Contactar</h2>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
        Habla directamente con {tecnico.full_name.split(' ')[0]}.
      </p>
      <Boton
        type="button"
        variante="exito"
        className="mt-4 w-full"
        onClick={() => dialogo.current.showModal()}
      >
        <MessageCircle className="size-4" aria-hidden="true" />
        Escribir por WhatsApp
      </Boton>

      <dialog
        ref={dialogo}
        aria-labelledby="titulo-autorizacion"
        className="m-auto w-[min(28rem,calc(100%-2rem))] rounded-2xl bg-white p-6 backdrop:bg-slate-900/50 dark:bg-slate-900"
      >
        <h3
          id="titulo-autorizacion"
          className="text-lg font-semibold text-slate-900 dark:text-white"
        >
          ¿Autorizas el contacto?
        </h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-200">
          <li>Se abrirá WhatsApp con un mensaje de saludo. Tu número lo verá el técnico.</li>
          <li>PrevenRed no guarda tu número ni la conversación.</li>
          <li>La conversación sigue fuera de la plataforma.</li>
        </ul>
        {contacto.error && (
          <div className="mt-3">
            <Alerta tipo="error">
              No se pudo abrir WhatsApp. {mensajeDeError(contacto.error)}
            </Alerta>
          </div>
        )}
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Boton type="button" variante="secundario" onClick={() => dialogo.current.close()}>
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
            <Boton type="button" cargando={contacto.isPending} onClick={() => contacto.mutate()}>
              Sí, autorizo
            </Boton>
          )}
        </div>
      </dialog>
    </section>
  )
}
