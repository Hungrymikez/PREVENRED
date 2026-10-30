import { Outlet } from 'react-router'
import { Cargando, SinResultados } from '@/components/ui/Estados'
import { Volver } from '@/components/ui/Volver'
import { useModo } from '@/hooks/useModo'

/** Los reportes solo están disponibles con el Modo Emergencia activo (CU-29 E3). */
export function RutaEmergencia() {
  const { cargando, enEmergencia } = useModo()

  if (cargando) return <Cargando />
  if (!enEmergencia) {
    return (
      <>
        <Volver a="/panel">Volver al inicio</Volver>
        <div className="mt-4">
          <SinResultados titulo="No hay una emergencia activa">
            Los reportes se habilitan cuando la entidad activa el Modo Emergencia. Si alguien está
            en peligro, llama al 123.
          </SinResultados>
        </div>
      </>
    )
  }
  return <Outlet />
}
