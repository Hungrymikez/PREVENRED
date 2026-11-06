import { nombreEstado } from '@/api/incidentes'
import { Etiqueta } from '@/components/ui/Etiqueta'

const COLOR = {
  REPORTADO: 'gris',
  EN_REVISION: 'ambar',
  ASIGNADO: 'azul',
  EN_ATENCION: 'azul',
  RESUELTO: 'verde',
}

export function EstadoCaso({ caso }) {
  return <Etiqueta color={COLOR[caso.status]}>{nombreEstado(caso.status, caso.categoria)}</Etiqueta>
}
