import { z } from 'zod'
import { CATEGORIAS, CONDICIONES, MODALIDADES } from '@/api/segundavida'
import { NOMBRES_ZONAS } from '@/utils/zonas'

/**
 * CU-11 · Publicar material. Los valores son los enums del backend (marketplace).
 * El precio solo es obligatorio en venta y alquiler: en una donación es 0.
 */
export const esquemaPublicacion = z
  .object({
    offerType: z.enum(Object.keys(MODALIDADES)),
    title: z.string().trim().min(3, 'Escribe un título de al menos 3 caracteres.').max(80),
    description: z
      .string()
      .trim()
      .min(10, 'Describe el material (mínimo 10 caracteres).')
      .max(1000),
    category: z.enum(Object.keys(CATEGORIAS), 'Elige una categoría.'),
    condition: z.enum(Object.keys(CONDICIONES), 'Elige el estado.'),
    quantity: z.coerce.number('Indica la cantidad.').positive('Debe ser mayor a 0.'),
    unit: z.string().trim().min(1, 'Indica la unidad.').max(20),
    price: z.coerce.number().min(0, 'El precio no puede ser negativo.'),
    zona: z.enum(NOMBRES_ZONAS, 'Elige tu barrio.'),
  })
  .refine((d) => d.offerType === 'DONACION' || d.price > 0, {
    message: 'Indica el precio.',
    path: ['price'],
  })
