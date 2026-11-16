import { Anvil, BrickWall, Droplets, Package, TreePine, Wrench, Zap } from 'lucide-react'

/** Un ícono por categoría del backend (MaterialCategory); OTROS usa el genérico. */
const ICONOS = {
  CONSTRUCCION: BrickWall,
  MADERA: TreePine,
  METAL: Anvil,
  ELECTRICO: Zap,
  PLOMERIA: Droplets,
  HERRAMIENTAS: Wrench,
}

/** Imagen de relleno para las publicaciones sin fotos (CU-47). */
export function IconoCategoria({ categoria, className = 'h-32' }) {
  const Icono = ICONOS[categoria] ?? Package
  return (
    <div
      className={`flex items-center justify-center rounded-lg bg-marca-50 dark:bg-amber-400/10 ${className}`}
    >
      <Icono className="size-10 text-marca-600 dark:text-amber-400" aria-hidden="true" />
    </div>
  )
}
