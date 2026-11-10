import { useQuery } from '@tanstack/react-query'
import { MapPin } from 'lucide-react'
import { useState } from 'react'
import { useParams } from 'react-router'
import { Circle } from 'react-leaflet'
import { CONDICIONES, MODALIDADES, obtenerPublicacion } from '@/api/segundavida'
import { Mapa } from '@/components/mapa/Mapa'
import { Alerta } from '@/components/ui/Alerta'
import { Cargando, ErrorAlCargar } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { Volver } from '@/components/ui/Volver'
import { formatearDistancia } from '@/utils/distancia'
import { IconoCategoria } from './IconoCategoria'
import { textoPrecio } from './precio'

/** CU-12, pasos 6-7: detalle de una publicación con su ubicación aproximada. */
export default function DetallePublicacion() {
  const { id } = useParams()
  const {
    data: p,
    isPending,
    error,
  } = useQuery({
    queryKey: ['publicacion', id],
    queryFn: () => obtenerPublicacion(id),
  })

  return (
    <>
      <Volver a="/segundavida">Volver a SegundaVida</Volver>

      <div className="mt-4">
        {isPending ? (
          <Cargando />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <Galeria publicacion={p} />
              <div className="mt-4 flex flex-wrap gap-1">
                <Etiqueta color="azul">{MODALIDADES[p.offerType].nombre}</Etiqueta>
                <Etiqueta>{p.category}</Etiqueta>
                <Etiqueta>{CONDICIONES[p.condition]}</Etiqueta>
              </div>
              <h1 className="mt-2 text-2xl font-bold text-slate-900">{p.title}</h1>
              <p className="mt-1 text-2xl font-bold text-marca-700">{textoPrecio(p)}</p>
              <p className="mt-4 text-slate-700">{p.description}</p>

              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-slate-500">Cantidad</dt>
                  <dd className="font-medium text-slate-900">{p.quantity}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Publicado por</dt>
                  <dd className="font-medium text-slate-900">{p.ownerName}</dd>
                </div>
              </dl>

              <div className="mt-6">
                <Alerta tipo="info">
                  Pronto podrás{' '}
                  {p.offerType === 'ALQUILER' ? 'solicitar el alquiler' : 'contactar al vecino'}{' '}
                  desde aquí. Esta función está en construcción.
                </Alerta>
              </div>
            </div>

            <div>
              <h2 className="flex items-center gap-1 font-semibold text-slate-900">
                <MapPin className="size-4" aria-hidden="true" />
                {p.zona} · {formatearDistancia(p.distanciaKm)}
              </h2>
              <p className="mb-2 text-sm text-slate-600">
                Ubicación aproximada: el barrio, nunca la dirección exacta.
              </p>
              <Mapa centro={p.coordenadas} zoom={14} className="h-72">
                <Circle center={p.coordenadas} radius={400} pathOptions={{ color: '#1d4ed8' }} />
              </Mapa>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

/** Foto grande con miniaturas para cambiarla; sin fotos, el ícono de la categoría. */
function Galeria({ publicacion: p }) {
  const [elegida, setElegida] = useState(0)
  const fotos = p.mediaUrls ?? []
  if (!fotos.length) return <IconoCategoria categoria={p.category} className="h-56" />

  return (
    <div>
      <img
        src={fotos[elegida]}
        alt={`Foto ${elegida + 1} de ${p.title}`}
        className="h-72 w-full rounded-lg bg-slate-100 object-contain"
      />
      {fotos.length > 1 && (
        <ul className="mt-2 flex gap-2 overflow-x-auto">
          {fotos.map((url, i) => (
            <li key={url} className="shrink-0">
              <button
                type="button"
                onClick={() => setElegida(i)}
                aria-label={`Ver foto ${i + 1}`}
                aria-pressed={i === elegida}
                className="block rounded-md ring-offset-2 aria-pressed:ring-2 aria-pressed:ring-marca-600"
              >
                <img src={url} alt="" className="size-16 rounded-md object-cover" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
