import { Link } from 'react-router'
import { Logo } from '@/components/Logo'

export default function Inicio() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-marca-50 px-4 dark:bg-amber-400/10">
      <div className="max-w-md text-center">
        <Logo />
        <p className="mt-4 text-slate-700 dark:text-slate-200">
          Resiliencia urbana, economía colaborativa y bienestar comunitario para Pereira.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link
            to="/login"
            className="rounded-lg bg-marca-600 px-5 py-2.5 font-medium text-white hover:bg-marca-700 dark:bg-amber-500 dark:text-slate-950 dark:hover:bg-amber-400"
          >
            Iniciar sesión
          </Link>
          <Link
            to="/registro"
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 font-medium text-slate-800 hover:bg-slate-50 dark:border-white/20 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-white/5"
          >
            Crear cuenta
          </Link>
        </div>
      </div>
    </main>
  )
}
