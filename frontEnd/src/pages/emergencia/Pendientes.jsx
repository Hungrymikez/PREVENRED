import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CloudOff, RotateCw, Trash2 } from 'lucide-react'
import { CATEGORIAS_REPORTE } from '@/api/incidentes'
import { Boton } from '@/components/ui/Boton'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { usePendientes } from '@/hooks/usePendientes'
import { eliminarPendiente, reintentarPendiente } from '@/offline/almacen'
import { formatearFecha } from '@/utils/fechas'

/** Reportes guardados en el celular que aún no llegan al servidor (CU-37 paso 3). */
export function Pendientes() {
  const { data: pendientes = [] } = usePendientes()
  const queryClient = useQueryClient()
  const recargar = () => queryClient.invalidateQueries({ queryKey: ['pendientes'] })

  const reintentar = useMutation({
    mutationFn: reintentarPendiente,
    onSuccess: recargar,
    networkMode: 'always',
  })
  const descartar = useMutation({
    mutationFn: eliminarPendiente,
    onSuccess: recargar,
    networkMode: 'always',
  })

  if (pendientes.length === 0) return null

  return (
    <section className="mt-6" aria-labelledby="titulo-pendientes">
      <h2 id="titulo-pendientes" className="flex items-center gap-2 font-semibold text-slate-900">
        <CloudOff className="size-5 text-amber-600" aria-hidden="true" />
        Guardados en este celular
      </h2>
      <p className="text-sm text-slate-600">Se envían solos cuando hay conexión.</p>

      <ul className="mt-3 divide-y divide-amber-100 rounded-2xl border border-amber-200 bg-amber-50">
        {pendientes.map(({ clientId, creadoEn, estado, error, datos }) => {
          const categoria = CATEGORIAS_REPORTE[datos.categoria]
          return (
            <li key={clientId} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-slate-900">
                    {categoria.titulo} · {categoria.tipos[datos.type]}
                  </p>
                  <p className="text-xs text-slate-500">Guardado el {formatearFecha(creadoEn)}</p>
                </div>
                {estado === 'error' ? (
                  <Etiqueta color="ambar">No se pudo enviar</Etiqueta>
                ) : (
                  <Etiqueta>Pendiente de envío</Etiqueta>
                )}
              </div>

              {estado === 'error' && (
                <>
                  <p className="mt-2 text-sm text-alerta-700">{error}</p>
                  <div className="mt-3 flex gap-2">
                    <Boton variante="secundario" onClick={() => reintentar.mutate(clientId)}>
                      <RotateCw className="size-4" aria-hidden="true" />
                      Reintentar
                    </Boton>
                    <Boton
                      variante="secundario"
                      onClick={() => {
                        if (window.confirm('¿Descartar este reporte? Se borrará de tu celular.')) {
                          descartar.mutate(clientId)
                        }
                      }}
                    >
                      <Trash2 className="size-4" aria-hidden="true" />
                      Descartar
                    </Boton>
                  </div>
                </>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
