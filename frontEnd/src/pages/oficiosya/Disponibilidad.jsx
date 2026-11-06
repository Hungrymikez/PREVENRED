import { Etiqueta } from '@/components/ui/Etiqueta'

export function Disponibilidad({ disponible }) {
  return disponible ? (
    <Etiqueta color="verde">Disponible</Etiqueta>
  ) : (
    <Etiqueta color="ambar">Ocupado</Etiqueta>
  )
}
