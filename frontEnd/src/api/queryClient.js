import { QueryClient } from '@tanstack/react-query'

/**
 * Caché de datos del servidor (TanStack Query).
 * Uso: const { data, isPending, error } = useQuery({ queryKey: ['incidentes'], queryFn: listarIncidentes })
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // durante 30 s se reutiliza lo que ya se trajo sin volver a pedirlo
      // Reintenta solo fallas de red o del servidor; un 4xx (permiso, no existe) no mejora reintentando.
      retry: (intentos, error) => intentos < 2 && !(error?.response?.status < 500),
    },
  },
})
