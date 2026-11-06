import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { registrar } from '@/api/auth'
import { mensajeDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { ROLES } from '@/utils/roles'
import { esquemaRegistro } from './esquemas'

const TIPOS_DE_CUENTA = [
  {
    valor: ROLES.CIUDADANO,
    titulo: 'Ciudadano',
    descripcion: 'Reporta incidentes, intercambia materiales y busca técnicos.',
  },
  {
    valor: ROLES.TECNICO_VOLUNTARIO,
    titulo: 'Técnico / voluntario',
    descripcion: 'Ofrece tus servicios o apoya en emergencias.',
  },
]

/** CU-01 · Registrarse. */
export default function Registro() {
  const navegar = useNavigate()
  const [errorServidor, setErrorServidor] = useState('')

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(esquemaRegistro),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      confirmar: '',
      role: ROLES.CIUDADANO,
      neighborhood: '',
      phone: '',
      skills: '',
      accepted_terms: false,
    },
  })
  const esTecnico = useWatch({ control, name: 'role' }) === ROLES.TECNICO_VOLUNTARIO

  async function enviar({ confirmar: _confirmar, skills, ...datos }) {
    setErrorServidor('')
    try {
      await registrar({
        ...datos,
        // "plomería, electricidad" -> ["plomería", "electricidad"]
        skills: esTecnico
          ? skills
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean)
          : [],
      })
      navegar('/login', { state: { registrado: true } })
    } catch (error) {
      setErrorServidor(mensajeDeError(error))
    }
  }

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900">Crea tu cuenta</h1>
      <p className="mt-1 text-sm text-slate-600">Únete a la red de prevención de Pereira.</p>

      <form onSubmit={handleSubmit(enviar)} noValidate className="mt-6 space-y-4">
        {errorServidor && <Alerta tipo="error">{errorServidor}</Alerta>}

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-800">Tipo de cuenta</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {TIPOS_DE_CUENTA.map((tipo) => (
              <label
                key={tipo.valor}
                className="cursor-pointer rounded-lg border border-slate-300 p-3 has-checked:border-marca-600 has-checked:bg-marca-50 has-focus-visible:ring-2 has-focus-visible:ring-marca-600"
              >
                <input type="radio" value={tipo.valor} className="sr-only" {...register('role')} />
                <span className="block font-medium text-slate-900">{tipo.titulo}</span>
                <span className="block text-xs text-slate-600">{tipo.descripcion}</span>
              </label>
            ))}
          </div>
          {errors.role && <p className="mt-1 text-sm text-alerta-700">{errors.role.message}</p>}
        </fieldset>

        <Campo
          etiqueta="Nombre completo"
          autoComplete="name"
          error={errors.full_name?.message}
          {...register('full_name')}
        />
        <Campo
          etiqueta="Correo electrónico"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <Campo
          etiqueta="Contraseña"
          type="password"
          autoComplete="new-password"
          ayuda="Mínimo 8 caracteres."
          error={errors.password?.message}
          {...register('password')}
        />
        <Campo
          etiqueta="Confirma la contraseña"
          type="password"
          autoComplete="new-password"
          error={errors.confirmar?.message}
          {...register('confirmar')}
        />
        <Campo
          etiqueta="Barrio o comuna"
          placeholder="Ej.: Cuba, comuna Villasantana"
          error={errors.neighborhood?.message}
          {...register('neighborhood')}
        />
        <Campo
          etiqueta="Teléfono (opcional)"
          type="tel"
          autoComplete="tel"
          error={errors.phone?.message}
          {...register('phone')}
        />
        {esTecnico && (
          <Campo
            etiqueta="Habilidades u oficios"
            placeholder="Ej.: plomería, electricidad, primeros auxilios"
            ayuda="Sepáralas con comas."
            error={errors.skills?.message}
            {...register('skills')}
          />
        )}

        <div>
          <label className="flex items-start gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              className="mt-0.5 size-4 accent-marca-600"
              aria-invalid={errors.accepted_terms ? 'true' : 'false'}
              {...register('accepted_terms')}
            />
            Acepto el aviso de privacidad y el tratamiento de mis datos personales.
          </label>
          {errors.accepted_terms && (
            <p className="mt-1 text-sm text-alerta-700">{errors.accepted_terms.message}</p>
          )}
        </div>

        <Boton type="submit" cargando={isSubmitting} className="w-full">
          Crear cuenta
        </Boton>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" className="font-medium text-marca-700 hover:underline">
          Inicia sesión
        </Link>
      </p>
    </>
  )
}
