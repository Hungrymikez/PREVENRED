import { BrickWall, Droplets, Package, PaintRoller, TreePine, Wrench, Zap } from 'lucide-react'

const ICONOS = {
  Construcción: BrickWall,
  Madera: TreePine,
  Eléctrico: Zap,
  Plomería: Droplets,
  Pintura: PaintRoller,
  Herramientas: Wrench,
}

/** Imagen de relleno mientras no existan las fotos de las publicaciones (CU-47). */
export function IconoCategoria({ categoria, className = 'h-32' }) {
  const Icono = ICONOS[categoria] ?? Package
  return (
    <div className={`flex items-center justify-center rounded-lg bg-marca-50 ${className}`}>
      <Icono className="size-10 text-marca-600" aria-hidden="true" />
    </div>
  )
}
