import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router'
import { mensajeDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { useAuth } from '@/hooks/useAuth'
import { esquemaLogin } from './esquemas'

/** CU-02 · Iniciar sesión. */
export default function Login() {
  const { iniciarSesion } = useAuth()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const [errorServidor, setErrorServidor] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(esquemaLogin), defaultValues: { email: '', password: '' } })

  async function enviar({ email, password }) {
    setErrorServidor('')
    try {
      await iniciarSesion(email, password)
      // Vuelve a la página que quería ver antes de que le pidieran iniciar sesión.
      navegar(ubicacion.state?.desde?.pathname ?? '/panel', { replace: true })
    } catch (error) {
      setErrorServidor(mensajeDeError(error))
    }
  }

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900">Inicia sesión</h1>
      <p className="mt-1 text-sm text-slate-600">Bienvenido de nuevo a PrevenRed.</p>

      {ubicacion.state?.registrado && (
        <div className="mt-4">
          <Alerta tipo="exito">Tu cuenta fue creada. Ya puedes iniciar sesión.</Alerta>
        </div>
      )}

      <form onSubmit={handleSubmit(enviar)} noValidate className="mt-6 space-y-4">
        {errorServidor && <Alerta tipo="error">{errorServidor}</Alerta>}

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
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />

        <Boton type="submit" cargando={isSubmitting} className="w-full">
          Entrar
        </Boton>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        ¿No tienes cuenta?{' '}
        <Link to="/registro" className="font-medium text-marca-700 hover:underline">
          Regístrate
        </Link>
      </p>
    </>
  )
}
