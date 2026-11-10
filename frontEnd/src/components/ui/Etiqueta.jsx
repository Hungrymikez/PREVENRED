const COLORES = {
  gris: 'bg-slate-100 dark:bg-white/10 text-slate-700 dark:text-slate-200',
  azul: 'bg-marca-100 text-marca-900 dark:bg-sky-400/15 dark:text-sky-200',
  verde: 'bg-green-100 text-green-800 dark:bg-green-400/15 dark:text-green-300',
  ambar: 'bg-amber-100 text-amber-900 dark:bg-amber-400/15 dark:text-amber-200',
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
