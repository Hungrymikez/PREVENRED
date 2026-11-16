import { formatearPesos } from '@/utils/distancia'

/** Texto del precio según la modalidad: venta, donación o alquiler por día. */
export function textoPrecio({ offerType, price }) {
  if (offerType === 'DONACION') return 'Gratis · donación'
  if (offerType === 'ALQUILER') return `${formatearPesos(price)} / día`
  return price === 0 ? 'Gratis' : formatearPesos(price)
}
