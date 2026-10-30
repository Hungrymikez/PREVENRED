const COLORES = {
  gris: 'bg-slate-100 text-slate-700',
  azul: 'bg-marca-100 text-marca-900',
  verde: 'bg-green-100 text-green-800',
  ambar: 'bg-amber-100 text-amber-900',
}

/** Etiqueta pequeña para estados y categorías. color: "gris" | "azul" | "verde" | "ambar". */
export function Etiqueta({ color = 'gris', children }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${COLORES[color]}`}
    >
      {children}
    </span>
  )
}
