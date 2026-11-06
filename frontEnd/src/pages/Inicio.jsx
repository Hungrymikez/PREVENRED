import { Link } from 'react-router'
import { Logo } from '@/components/Logo'

export default function Inicio() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-marca-50 px-4">
      <div className="max-w-md text-center">
        <Logo />
        <p className="mt-4 text-slate-700">
          Resiliencia urbana, economía colaborativa y bienestar comunitario para Pereira.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link
            to="/login"
            className="rounded-lg bg-marca-600 px-5 py-2.5 font-medium text-white hover:bg-marca-700"
          >
            Iniciar sesión
          </Link>
          <Link
            to="/registro"
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 font-medium text-slate-800 hover:bg-slate-50"
          >
            Crear cuenta
          </Link>
        </div>
      </div>
    </main>
  )
}
