import { ESTADOS_VERIFICACION } from '@/api/oficiosya'
import { Etiqueta } from '@/components/ui/Etiqueta'

const COLOR = { PENDIENTE: 'ambar', VERIFICADO: 'verde', RECHAZADO: 'gris' }

/** Estado de verificación del perfil técnico (CU-17, CU-18). */
export function EstadoVerificacion({ estado }) {
  return (
    <Etiqueta color={COLOR[estado] ?? 'gris'}>{ESTADOS_VERIFICACION[estado] ?? estado}</Etiqueta>
  )
}
