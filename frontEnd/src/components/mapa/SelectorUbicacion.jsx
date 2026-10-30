import { LocateFixed } from 'lucide-react'
import { useEffect } from 'react'
import { Marker, useMap, useMapEvents } from 'react-leaflet'
import { Mapa } from '@/components/mapa/Mapa'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { useUbicacion } from '@/hooks/useUbicacion'

/**
 * Elegir un punto: con el GPS (CU-48) o tocando el mapa (CU-29 A2, CU-30 E1).
 * `valor` es [lat, lng] o null.
 */
export function SelectorUbicacion({ valor, onCambiar, error }) {
  const gps = useUbicacion()

  return (
    <div className="space-y-3">
      <Boton
        type="button"
        variante="secundario"
        cargando={gps.buscando}
        onClick={() => gps.pedir(onCambiar)}
        className="w-full"
      >
        <LocateFixed className="size-4" aria-hidden="true" />
        Usar mi ubicación actual
      </Boton>
      {gps.error && <Alerta tipo="error">{gps.error} Marca el lugar tocando el mapa.</Alerta>}

      <p className="text-sm text-slate-600">
        {valor
          ? 'Puedes tocar el mapa para corregir el punto.'
          : 'O toca el mapa donde está el problema.'}
      </p>
      <Mapa className="h-72">
        <ElegirConClic onCambiar={onCambiar} />
        {valor && (
          <>
            <Marker position={valor} />
            <Centrar en={valor} />
          </>
        )}
      </Mapa>
      {error && <p className="text-sm text-alerta-700">{error}</p>}
    </div>
  )
}

function ElegirConClic({ onCambiar }) {
  useMapEvents({ click: (e) => onCambiar([e.latlng.lat, e.latlng.lng]) })
  return null
}

/** Mueve el mapa al punto elegido (por ejemplo, cuando llega la ubicación del GPS). */
function Centrar({ en }) {
  const mapa = useMap()
  useEffect(() => {
    mapa.setView(en, Math.max(mapa.getZoom(), 16))
  }, [mapa, en])
  return null
}
