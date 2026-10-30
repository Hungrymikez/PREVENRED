import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { BadgeCheck, MapPin } from 'lucide-react'
import { Link } from 'react-router'
import { Marker, Popup } from 'react-leaflet'
import { ESPECIALIDADES, listarTecnicos } from '@/api/oficiosya'
import { Mapa } from '@/components/mapa/Mapa'
import { SelectorVista } from '@/components/SelectorVista'
import { Campo } from '@/components/ui/Campo'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Estrellas } from '@/components/ui/Estrellas'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { useFiltrosUrl } from '@/hooks/useFiltrosUrl'
import { NOMBRES_ZONAS } from '@/utils/zonas'
import { Disponibilidad } from './Disponibilidad'

/** CU-19 · Buscar servicios técnicos (solo técnicos verificados). */
export default function OficiosYa() {
  const [filtros, cambiar] = useFiltrosUrl()
  const { vista = 'lista', ...consulta } = filtros

  const {
    data: tecnicos,
    isPending,
    error,
  } = useQuery({
    queryKey: ['tecnicos', consulta],
    queryFn: () => listarTecnicos(consulta),
    placeholderData: keepPreviousData,
  })

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900">OficiosYa Pereira</h1>
      <p className="text-slate-600">Técnicos verificados cerca de ti.</p>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Campo
          etiqueta="¿Qué necesitas arreglar?"
          type="search"
          placeholder="Ej.: fuga, enchufe, gotera"
          value={filtros.texto ?? ''}
          onChange={(e) => cambiar('texto', e.target.value)}
        />
        <Campo
          como="select"
          etiqueta="Especialidad"
          value={filtros.especialidad ?? ''}
          onChange={(e) => cambiar('especialidad', e.target.value)}
        >
          <option value="">Todas</option>
          {ESPECIALIDADES.map((e) => (
            <option key={e}>{e}</option>
          ))}
        </Campo>
        <Campo
          como="select"
          etiqueta="Zona"
          value={filtros.zona ?? ''}
          onChange={(e) => cambiar('zona', e.target.value)}
        >
          <option value="">Toda Pereira</option>
          {NOMBRES_ZONAS.map((z) => (
            <option key={z}>{z}</option>
          ))}
        </Campo>
        <Campo
          como="select"
          etiqueta="Valoración mínima"
          value={filtros.valoracionMin ?? ''}
          onChange={(e) => cambiar('valoracionMin', e.target.value)}
        >
          <option value="">Cualquiera</option>
          <option value="4.5">4,5 o más</option>
          <option value="4">4 o más</option>
        </Campo>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            className="size-4 accent-marca-600"
            checked={filtros.soloDisponibles === 'si'}
            onChange={(e) => cambiar('soloDisponibles', e.target.checked && 'si')}
          />
          Solo disponibles ahora
        </label>
        <SelectorVista vista={vista} onCambiar={(v) => cambiar('vista', v)} />
      </div>

      <div className="mt-3">
        {isPending ? (
          <Cargando texto="Buscando técnicos…" />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : tecnicos.length === 0 ? (
          <SinResultados>Prueba con otra especialidad o amplía la zona.</SinResultados>
        ) : vista === 'mapa' ? (
          <Mapa className="h-[28rem]">
            {tecnicos.map((t) => (
              <Marker key={t.id} position={t.coordenadas}>
                <Popup>
                  <Link to={`/oficiosya/${t.id}`} className="font-medium">
                    {t.fullName}
                  </Link>
                  <br />
                  {t.specialties.join(', ')} · {t.zona}
                </Popup>
              </Marker>
            ))}
          </Mapa>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2">
            {tecnicos.map((t) => (
              <li key={t.id}>
                <TarjetaTecnico tecnico={t} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}

function TarjetaTecnico({ tecnico: t }) {
  return (
    <Link
      to={`/oficiosya/${t.id}`}
      className="flex h-full gap-3 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-marca-600 hover:shadow-sm"
    >
      <div
        className="flex size-12 shrink-0 items-center justify-center rounded-full bg-marca-100 font-bold text-marca-900"
        aria-hidden="true"
      >
        {t.fullName
          .split(' ')
          .map((n) => n[0])
          .join('')}
      </div>
      <div className="min-w-0">
        <h2 className="flex items-center gap-1 font-semibold text-slate-900">
          {t.fullName}
          <BadgeCheck className="size-4 text-marca-600" aria-label="Verificado" />
        </h2>
        <div className="mt-1 flex flex-wrap gap-1">
          {t.specialties.map((e) => (
            <Etiqueta key={e} color="azul">
              {e}
            </Etiqueta>
          ))}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
          <Estrellas valor={t.rating} total={t.totalReviews} />
          <span className="flex items-center gap-1 text-sm text-slate-600">
            <MapPin className="size-4" aria-hidden="true" />
            {t.zona}
          </span>
          <Disponibilidad disponible={t.disponible} />
        </div>
      </div>
    </Link>
  )
}
