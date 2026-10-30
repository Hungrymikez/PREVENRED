import { LogOut } from 'lucide-react'
import { Suspense } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router'
import { BannerEmergencia } from '@/components/BannerEmergencia'
import { Logo } from '@/components/Logo'
import { SimuladorModo } from '@/components/SimuladorModo'
import { Boton } from '@/components/ui/Boton'
import { Cargando } from '@/components/ui/Estados'
import { useAuth } from '@/hooks/useAuth'
import { useModo } from '@/hooks/useModo'
import { MODULOS, MODULOS_EMERGENCIA } from '@/utils/modulos'
import { NOMBRE_ROL } from '@/utils/roles'

/**
 * Marco de las páginas con sesión: barra superior con el usuario y el menú.
 * En celular el menú va abajo (barra fija), en pantallas grandes va en la barra superior.
 * En Modo Emergencia muestra el aviso rojo y cambia el menú (RF-02).
 */
export function LayoutPrincipal() {
  const { usuario, cerrarSesion } = useAuth()
  const navegar = useNavigate()
  const { modo, enEmergencia } = useModo()
  const menu = enEmergencia ? MODULOS_EMERGENCIA : MODULOS

  function salir() {
    cerrarSesion()
    navegar('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <Logo a="/panel" />
          <nav aria-label="Principal" className="hidden md:block">
            <ul className="flex gap-1">
              {menu.map(({ ruta, nombre, exacta }) => (
                <li key={ruta}>
                  <NavLink
                    to={ruta}
                    end={exacta}
                    className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 aria-[current=page]:bg-marca-50 aria-[current=page]:text-marca-700"
                  >
                    {nombre}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="flex items-center gap-3">
            <div className="hidden text-right lg:block">
              <p className="text-sm font-medium text-slate-900">{usuario.full_name}</p>
              <p className="text-xs text-slate-500">{NOMBRE_ROL[usuario.role] ?? usuario.role}</p>
            </div>
            <Boton variante="secundario" onClick={salir} aria-label="Cerrar sesión">
              <LogOut className="size-4" aria-hidden="true" />
              <span className="hidden sm:inline">Salir</span>
            </Boton>
          </div>
        </div>
      </header>
      {enEmergencia && <BannerEmergencia modo={modo} />}

      <main className="mx-auto max-w-5xl px-4 pt-6 pb-24 md:pb-10">
        {/* Al cambiar de sección solo el contenido muestra "Cargando", el menú se queda. */}
        <Suspense fallback={<Cargando />}>
          <Outlet />
        </Suspense>
      </main>

      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200 bg-white md:hidden"
      >
        <ul className="grid grid-cols-4">
          {menu.map(({ ruta, nombre, Icono, exacta }) => (
            <li key={ruta}>
              <NavLink
                to={ruta}
                end={exacta}
                className="flex flex-col items-center gap-0.5 py-2 text-xs font-medium text-slate-500 aria-[current=page]:text-marca-700"
              >
                <Icono className="size-5" aria-hidden="true" />
                {nombre}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <SimuladorModo />
    </div>
  )
}
