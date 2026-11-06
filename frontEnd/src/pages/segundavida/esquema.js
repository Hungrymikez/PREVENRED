import { z } from 'zod'
import { CATEGORIAS, CONDICIONES } from '@/api/segundavida'
import { NOMBRES_ZONAS } from '@/utils/zonas'

/** CU-11 · Publicar material. El precio solo es obligatorio en venta y alquiler. */
export const esquemaPublicacion = z
  .object({
    offerType: z.enum(['VENTA', 'INTERCAMBIO', 'ALQUILER']),
    title: z.string().trim().min(3, 'Escribe un título de al menos 3 caracteres.').max(80),
    description: z
      .string()
      .trim()
      .min(10, 'Describe el material (mínimo 10 caracteres).')
      .max(1000),
    category: z.enum(CATEGORIAS, 'Elige una categoría.'),
    condition: z.enum(Object.keys(CONDICIONES), 'Elige el estado.'),
    quantity: z.coerce
      .number('Indica la cantidad.')
      .int('Debe ser un número entero.')
      .min(1, 'Mínimo 1.'),
    price: z.coerce.number().min(0, 'El precio no puede ser negativo.'),
    zona: z.enum(NOMBRES_ZONAS, 'Elige tu barrio.'),
  })
  .refine((d) => d.offerType === 'INTERCAMBIO' || d.price > 0, {
    message: 'Indica el precio.',
    path: ['price'],
  })
