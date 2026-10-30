import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { MapPin, Plus } from 'lucide-react'
import { Link } from 'react-router'
import { Marker, Popup } from 'react-leaflet'
import { CATEGORIAS, CONDICIONES, listarPublicaciones, MODALIDADES } from '@/api/segundavida'
import { Mapa } from '@/components/mapa/Mapa'
import { SelectorVista } from '@/components/SelectorVista'
import { Campo } from '@/components/ui/Campo'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { useFiltrosUrl } from '@/hooks/useFiltrosUrl'
import { formatearDistancia } from '@/utils/distancia'
import { IconoCategoria } from './IconoCategoria'
import { textoPrecio } from './precio'

/** CU-12 · Buscar materiales por ubicación. */
export default function SegundaVida() {
  const [filtros, cambiar] = useFiltrosUrl()
  const { vista = 'lista', ...resto } = filtros
  const modalidad = filtros.modalidad ?? 'VENTA'
  const consulta = { ...resto, modalidad }

  const {
    data: publicaciones,
    isPending,
    error,
  } = useQuery({
    queryKey: ['publicaciones', consulta],
    queryFn: () => listarPublicaciones(consulta),
    placeholderData: keepPreviousData, // mientras escribe, deja ver los resultados anteriores
  })

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">SegundaVida Pereira</h1>
          <p className="text-slate-600">Materiales y herramientas de tus vecinos.</p>
        </div>
        <Link
          to="/segundavida/publicar"
          className="inline-flex items-center gap-2 rounded-lg bg-marca-600 px-4 py-2.5 font-medium text-white hover:bg-marca-700"
        >
          <Plus className="size-4" aria-hidden="true" />
          Publicar
        </Link>
      </div>

      {/* Pestañas Comprar / Intercambiar / Alquilar */}
      <div
        className="mt-5 flex gap-1 border-b border-slate-200"
        role="group"
        aria-label="Modalidad"
      >
        {Object.entries(MODALIDADES).map(([valor, { pestana }]) => (
          <button
            key={valor}
            type="button"
            aria-pressed={modalidad === valor}
            onClick={() => cambiar('modalidad', valor)}
            className="-mb-px border-b-2 border-transparent px-4 py-2 font-medium text-slate-600 hover:text-slate-900 aria-pressed:border-marca-600 aria-pressed:text-marca-700"
          >
            {pestana}
          </button>
        ))}
      </div>

      {/* Filtros */}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Campo
          etiqueta="Buscar"
          type="search"
          placeholder="Ej.: ladrillo, taladro"
          value={filtros.texto ?? ''}
          onChange={(e) => cambiar('texto', e.target.value)}
        />
        <Campo
          como="select"
          etiqueta="Categoría"
          value={filtros.categoria ?? ''}
          onChange={(e) => cambiar('categoria', e.target.value)}
        >
          <option value="">Todas</option>
          {CATEGORIAS.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </Campo>
        <Campo
          como="select"
          etiqueta="Estado"
          value={filtros.condicion ?? ''}
          onChange={(e) => cambiar('condicion', e.target.value)}
        >
          <option value="">Cualquiera</option>
          {Object.entries(CONDICIONES).map(([valor, nombre]) => (
            <option key={valor} value={valor}>
              {nombre}
            </option>
          ))}
        </Campo>
        {modalidad !== 'INTERCAMBIO' && (
          <Campo
            etiqueta={modalidad === 'ALQUILER' ? 'Precio máximo por día' : 'Precio máximo'}
            type="number"
            min="0"
            step="1000"
            inputMode="numeric"
            placeholder="Sin límite"
            value={filtros.precioMax ?? ''}
            onChange={(e) => cambiar('precioMax', e.target.value)}
          />
        )}
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <p className="text-sm text-slate-600" aria-live="polite">
          {publicaciones && `${publicaciones.length} publicaciones · más cercanas primero`}
        </p>
        <SelectorVista vista={vista} onCambiar={(v) => cambiar('vista', v)} />
      </div>

      <div className="mt-3">
        {isPending ? (
          <Cargando texto="Buscando publicaciones…" />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : publicaciones.length === 0 ? (
          <SinResultados>Prueba quitando filtros o buscando en otra pestaña.</SinResultados>
        ) : vista === 'mapa' ? (
          <Mapa className="h-[28rem]">
            {publicaciones.map((p) => (
              <Marker key={p.id} position={p.coordenadas}>
                <Popup>
                  <Link to={`/segundavida/${p.id}`} className="font-medium">
                    {p.title}
                  </Link>
                  <br />
                  {textoPrecio(p)} · {p.zona}
                </Popup>
              </Marker>
            ))}
          </Mapa>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {publicaciones.map((p) => (
              <li key={p.id}>
                <TarjetaPublicacion publicacion={p} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}

function TarjetaPublicacion({ publicacion: p }) {
  return (
    <Link
      to={`/segundavida/${p.id}`}
      className="block h-full rounded-xl border border-slate-200 bg-white p-3 transition hover:border-marca-600 hover:shadow-sm"
    >
      <IconoCategoria categoria={p.category} />
      <div className="mt-3 flex flex-wrap gap-1">
        <Etiqueta color="azul">{p.category}</Etiqueta>
        <Etiqueta>{CONDICIONES[p.condition]}</Etiqueta>
      </div>
      <h2 className="mt-2 font-semibold text-slate-900">{p.title}</h2>
      <p className="mt-1 text-lg font-bold text-marca-700">{textoPrecio(p)}</p>
      <p className="mt-1 flex items-center gap-1 text-sm text-slate-600">
        <MapPin className="size-4" aria-hidden="true" />
        {p.zona} · {formatearDistancia(p.distanciaKm)}
      </p>
    </Link>
  )
}
