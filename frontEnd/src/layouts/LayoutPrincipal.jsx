import { LogOut } from 'lucide-react'
import { Suspense } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router'
import { BannerEmergencia } from '@/components/BannerEmergencia'
import { InterruptorTema } from '@/components/InterruptorTema'
import { Logo } from '@/components/Logo'
import { Sincronizador } from '@/components/Sincronizador'
import { Cargando } from '@/components/ui/Estados'
import { useAuth } from '@/hooks/useAuth'
import { useModo } from '@/hooks/useModo'
import { useTema } from '@/hooks/useTema'
import { MODULOS, MODULOS_EMERGENCIA, modulosParaRol } from '@/utils/modulos'
import { esPersonal, NOMBRE_ROL } from '@/utils/roles'

/**
 * Marco de las páginas con sesión: barra superior con el usuario y el menú.
 * En celular el menú va abajo (barra fija), en pantallas grandes va en la barra superior.
 * En Modo Emergencia muestra el aviso rojo y cambia el menú (RF-02).
 * El menú depende del rol: el personal de atención ve la bandeja de Casos en vez de Reportar.
 */
export function LayoutPrincipal() {
  const { usuario, cerrarSesion } = useAuth()
  const navegar = useNavigate()
  const { modo, enEmergencia } = useModo()
  const { oscuro, alternar } = useTema()
  // Cada rol ve solo sus secciones (el backend vuelve a validar cada permiso).
  const menu = modulosParaRol(enEmergencia ? MODULOS_EMERGENCIA : MODULOS, usuario.role).filter(
    (m) => !m.soloPanel,
  )

  function salir() {
    cerrarSesion()
    navegar('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/85">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <Logo a="/panel" />
          <nav aria-label="Principal" className="hidden md:block">
            <ul className="flex gap-1">
              {menu.map(({ ruta, nombre, exacta }) => (
                <li key={ruta}>
                  <NavLink
                    to={ruta}
                    end={exacta}
                    className="rounded-full px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 aria-[current=page]:bg-marca-600 aria-[current=page]:text-white dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white dark:aria-[current=page]:bg-amber-500 dark:aria-[current=page]:text-slate-950"
                  >
                    {nombre}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="flex items-center gap-3">
            <div className="hidden text-right lg:block">
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                {usuario.full_name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {NOMBRE_ROL[usuario.role] ?? usuario.role}
              </p>
            </div>
            <InterruptorTema oscuro={oscuro} onAlternar={alternar} />
            <span
              aria-hidden="true"
              className="hidden size-9 items-center justify-center rounded-full bg-marca-100 text-sm font-semibold text-marca-700 sm:flex dark:bg-amber-400/15 dark:text-amber-400"
            >
              {iniciales(usuario.full_name)}
            </span>
            <button
              type="button"
              onClick={salir}
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
              className="flex size-9 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:ring-2 focus-visible:ring-marca-600 focus-visible:outline-none dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-white dark:focus-visible:ring-amber-400"
            >
              <LogOut className="size-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>
      {enEmergencia && <BannerEmergencia modo={modo} puedeReportar={!esPersonal(usuario.role)} />}
      <Sincronizador />

      <main className="mx-auto max-w-5xl px-4 pt-6 pb-24 md:pb-10">
        {/* Al cambiar de sección solo el contenido muestra "Cargando", el menú se queda. */}
        <Suspense fallback={<Cargando />}>
          <Outlet />
        </Suspense>
      </main>

      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200/80 bg-white/90 pb-[env(safe-area-inset-bottom)] backdrop-blur-md md:hidden dark:border-white/10 dark:bg-slate-900/90"
      >
        <ul
          className="grid"
          style={{ gridTemplateColumns: `repeat(${menu.length}, minmax(0, 1fr))` }}
        >
          {menu.map(({ ruta, nombre, Icono, exacta }) => (
            <li key={ruta}>
              <NavLink
                to={ruta}
                end={exacta}
                className="group flex flex-col items-center gap-1 py-2 text-xs font-medium text-slate-500 aria-[current=page]:text-marca-700 dark:text-slate-400 dark:aria-[current=page]:text-amber-400"
              >
                <span className="flex h-7 w-12 items-center justify-center rounded-full transition group-aria-[current=page]:bg-marca-100 dark:group-aria-[current=page]:bg-amber-400/15">
                  <Icono className="size-5" aria-hidden="true" />
                </span>
                {nombre}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}

/** "Sara Salas" -> "SS"; un solo nombre -> su primera letra. */
function iniciales(nombre = '') {
  return nombre
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0].toUpperCase())
    .join('')
}
