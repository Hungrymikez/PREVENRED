import { useMutation, useQueryClient } from '@tanstack/react-query'
import { simularCambioDeModo } from '@/api/modo'
import { useModo } from '@/hooks/useModo'

/**
 * SOLO EN DESARROLLO (npm run dev): botón para probar la app en ambos modos.
 * En producción no se muestra; el cambio real lo hace un Administrador (CU-04).
 */
export function SimuladorModo() {
  const { enEmergencia } = useModo()
  const queryClient = useQueryClient()
  const cambio = useMutation({
    mutationFn: () => simularCambioDeModo(!enEmergencia),
    onSuccess: (modo) => queryClient.setQueryData(['modo'], modo),
  })

  if (!import.meta.env.DEV) return null

  return (
    <button
      type="button"
      onClick={() => cambio.mutate()}
      disabled={cambio.isPending}
      className="fixed right-3 bottom-20 z-20 rounded-full border border-dashed border-slate-400 bg-white/95 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-white md:bottom-4"
    >
      Demo: {enEmergencia ? 'volver a Cotidiano' : 'activar emergencia'}
    </button>
  )
}
