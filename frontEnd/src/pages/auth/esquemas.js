import { z } from 'zod'
import { ROLES } from '@/utils/roles'

// Las reglas reflejan las del backend (auth/interface/schemas.py y auth/domain).
// Validar aquí da respuesta inmediata; el backend igual vuelve a validar todo.

export const esquemaLogin = z.object({
  email: z.string().trim().min(1, 'Escribe tu correo.'),
  password: z.string().min(1, 'Escribe tu contraseña.'),
})

export const esquemaRegistro = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(3, 'Escribe tu nombre completo.')
      .max(150, 'Máximo 150 caracteres.'),
    email: z.email('El correo no tiene un formato válido.').max(254),
    password: z
      .string()
      .min(8, 'La contraseña debe tener al menos 8 caracteres.')
      .max(128, 'Máximo 128 caracteres.'),
    confirmar: z.string(),
    role: z.enum([ROLES.CIUDADANO, ROLES.TECNICO_VOLUNTARIO], 'Elige un tipo de cuenta.'),
    neighborhood: z.string().trim().min(1, 'Indica tu barrio o comuna.').max(100),
    phone: z.string().trim().max(20, 'Máximo 20 caracteres.'),
    skills: z.string(),
    accepted_terms: z.boolean().refine((v) => v, 'Debes aceptar el aviso de privacidad.'),
  })
  .refine((d) => d.password === d.confirmar, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmar'],
  })
