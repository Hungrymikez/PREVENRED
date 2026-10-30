import { formatearPesos } from '@/utils/distancia'

/** Texto del precio según la modalidad: venta, intercambio o alquiler por día. */
export function textoPrecio({ offerType, price }) {
  if (offerType === 'INTERCAMBIO') return 'Para intercambio'
  if (offerType === 'ALQUILER') return `${formatearPesos(price)} / día`
  return price === 0 ? 'Gratis' : formatearPesos(price)
}
