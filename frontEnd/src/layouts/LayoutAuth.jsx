import { Outlet } from 'react-router'
import { Logo } from '@/components/Logo'

/** Marco de las páginas de login y registro: tarjeta centrada. */
export function LayoutAuth() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-marca-50 px-4 py-10">
      <div className="mb-6">
        <Logo />
      </div>
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-sm sm:p-8">
        <Outlet />
      </div>
    </main>
  )
}
