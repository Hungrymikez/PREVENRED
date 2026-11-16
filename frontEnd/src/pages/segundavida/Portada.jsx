import { IconoCategoria } from './IconoCategoria'

/** Primera foto de la publicación; si no tiene, el ícono de su categoría. */
export function Portada({ publicacion: p, className = 'h-32' }) {
  const foto = p.mediaUrls?.[0]
  if (!foto) return <IconoCategoria categoria={p.category} className={className} />
  return (
    <img
      src={foto}
      alt={`Foto de ${p.title}`}
      className={`w-full rounded-lg bg-slate-100 object-cover ${className}`}
    />
  )
}
