import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldAlert, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { mensajeDeError } from '@/api/client'
import { cambiarModo } from '@/api/modo'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { useModo } from '@/hooks/useModo'

const MOTIVO_MINIMO = 10

/**
 * CU-04 · Cambiar modo operacional. Solo lo muestra el panel del Administrador (RN-01)
 * y el backend lo vuelve a validar. Pide un motivo, que queda en el historial (RN-02).
 */
export function ControlModo() {
  const { enEmergencia } = useModo()
  const queryClient = useQueryClient()
  const [abierto, setAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [error, setError] = useState('')

  const cambio = useMutation({
    mutationFn: () => cambiarModo({ activarEmergencia: !enEmergencia, motivo: motivo.trim() }),
    onSuccess: (modo) => {
      queryClient.setQueryData(['modo'], modo)
      queryClient.invalidateQueries({ queryKey: ['modo'] })
      setAbierto(false)
      setMotivo('')
    },
  })

  function confirmar(e) {
    e.preventDefault()
    if (motivo.trim().length < MOTIVO_MINIMO) {
      setError(`Escribe el motivo (mínimo ${MOTIVO_MINIMO} caracteres).`)
      return
    }
    setError('')
    cambio.mutate()
  }

  const Icono = enEmergencia ? ShieldAlert : ShieldCheck

  return (
    <section
      aria-labelledby="titulo-control-modo"
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span
            className={`flex size-11 items-center justify-center rounded-xl ${
              enEmergencia
                ? 'bg-alerta-50 text-alerta-700 dark:bg-red-950/50 dark:text-red-300'
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-400/15 dark:text-emerald-300'
            }`}
          >
            <Icono className="size-6" aria-hidden="true" />
          </span>
          <div>
            <h2 id="titulo-control-modo" className="font-semibold text-slate-900 dark:text-white">
              Modo de la plataforma
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {enEmergencia
                ? 'Modo Emergencia activo: los ciudadanos pueden reportar daños y pedir ayuda.'
                : 'Modo cotidiano. Activa la emergencia cuando la ciudad lo necesite.'}
            </p>
          </div>
        </div>
        {!abierto && (
          <Boton
            variante={enEmergencia ? 'secundario' : 'peligro'}
            onClick={() => setAbierto(true)}
          >
            {enEmergencia ? 'Volver a modo cotidiano' : 'Activar Modo Emergencia'}
          </Boton>
        )}
      </div>

      {abierto && (
        <form onSubmit={confirmar} noValidate className="mt-4 space-y-3">
          {cambio.error && <Alerta tipo="error">{mensajeDeError(cambio.error)}</Alerta>}
          <Campo
            como="textarea"
            rows={2}
            etiqueta={enEmergencia ? 'Motivo para cerrar la emergencia' : 'Motivo de la emergencia'}
            placeholder={
              enEmergencia
                ? 'Ej.: Se superó la emergencia; los equipos terminaron la atención.'
                : 'Ej.: Sismo de magnitud 5,8 sentido en Pereira.'
            }
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            error={error}
            ayuda="Queda registrado en el historial junto con tu nombre."
          />
          <div className="flex flex-wrap gap-2">
            <Boton
              type="submit"
              variante={enEmergencia ? 'primario' : 'peligro'}
              cargando={cambio.isPending}
            >
              {enEmergencia ? 'Confirmar cierre' : 'Confirmar activación'}
            </Boton>
            <Boton
              type="button"
              variante="secundario"
              onClick={() => {
                setAbierto(false)
                setError('')
                cambio.reset()
              }}
            >
              Cancelar
            </Boton>
          </div>
        </form>
      )}
    </section>
  )
}
