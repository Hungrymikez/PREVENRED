import { Moon, Sun } from 'lucide-react'

/** Interruptor de tema: sol (claro) o luna (oscuro). */
export function InterruptorTema({ oscuro, onAlternar, className = '' }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={oscuro}
      aria-label="Modo oscuro"
      title={oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      onClick={onAlternar}
      className={`relative inline-flex h-9 w-17 shrink-0 items-center rounded-full bg-white/85 p-1 shadow-lg ring-1 ring-black/10 backdrop-blur-sm transition-colors focus-visible:ring-2 focus-visible:ring-marca-600 focus-visible:outline-none dark:bg-slate-900/80 dark:ring-white/20 dark:focus-visible:ring-amber-400 ${className}`}
    >
      <Sun className="absolute left-2 size-4 text-amber-500" aria-hidden="true" />
      <Moon
        className="absolute right-2 size-4 text-slate-400 dark:text-amber-300"
        aria-hidden="true"
      />
      <span
        aria-hidden="true"
        className={`relative z-10 flex size-7 items-center justify-center rounded-full bg-white shadow transition-transform duration-200 dark:bg-slate-700 ${oscuro ? 'translate-x-8' : 'translate-x-0'}`}
      >
        {oscuro ? (
          <Moon className="size-4 text-amber-300" />
        ) : (
          <Sun className="size-4 text-amber-500" />
        )}
      </span>
    </button>
  )
}
