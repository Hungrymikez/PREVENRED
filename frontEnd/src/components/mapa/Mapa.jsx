import L from 'leaflet'
import iconoRetina from 'leaflet/dist/images/marker-icon-2x.png'
import icono from 'leaflet/dist/images/marker-icon.png'
import sombra from 'leaflet/dist/images/marker-shadow.png'
import 'leaflet/dist/leaflet.css'
import { MapContainer, TileLayer } from 'react-leaflet'
import { CENTRO_PEREIRA, ZOOM_INICIAL } from '@/utils/mapa'

// Con Vite, Leaflet no encuentra solo las imágenes del marcador: se le indican aquí.
L.Icon.Default.mergeOptions({ iconRetinaUrl: iconoRetina, iconUrl: icono, shadowUrl: sombra })

/**
 * Mapa base con OpenStreetMap. Las capas (marcadores, zonas) van como hijos:
 * <Mapa><Marker position={[lat, lng]} /></Mapa>
 */
export function Mapa({
  centro = CENTRO_PEREIRA,
  zoom = ZOOM_INICIAL,
  className = 'h-80',
  children,
}) {
  return (
    <MapContainer
      center={centro}
      zoom={zoom}
      scrollWheelZoom={false}
      className={`z-0 w-full rounded-xl ${className}`}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {children}
    </MapContainer>
  )
}
