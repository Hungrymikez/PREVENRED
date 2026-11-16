import { ImagePlus, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { agregarFotos, MAXIMO_FOTOS, TIPOS_FOTO } from './fotos'

/**
 * Fotos opcionales de la publicación (CU-11 con CU-47): hasta 5, con vista previa
 * y opción de quitar cada una antes de publicar (A2). Se suben al backend al publicar.
 */
export function SelectorFotos({ fotos, onCambiar }) {
  const [error, setError] = useState('')
  const vistasPrevias = useMemo(() => fotos.map((f) => URL.createObjectURL(f)), [fotos])
  // Libera la memoria de las vistas previas al cambiar las fotos o salir del formulario.
  useEffect(() => () => vistasPrevias.forEach((url) => URL.revokeObjectURL(url)), [vistasPrevias])

  function elegir(e) {
    const archivos = [...(e.target.files ?? [])]
    e.target.value = ''
    if (!archivos.length) return
    const resultado = agregarFotos(fotos, archivos)
    setError(resultado.error)
    onCambiar(resultado.fotos)
  }

  function quitar(indice) {
    setError('')
    onCambiar(fotos.filter((_, i) => i !== indice))
  }

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-100">
        Fotos (opcional, hasta {MAXIMO_FOTOS})
      </p>
      <ul className="grid grid-cols-3 gap-2 sm:grid-cols-5">
        {vistasPrevias.map((url, i) => (
          <li key={url} className="relative">
            <img
              src={url}
              alt={`Foto ${i + 1} de la publicación`}
              className="aspect-square w-full rounded-lg bg-slate-100 object-cover dark:bg-slate-800"
            />
            <button
              type="button"
              onClick={() => quitar(i)}
              className="absolute top-1 right-1 rounded-full bg-white/90 p-1 text-slate-700 shadow hover:bg-white dark:bg-slate-900/90 dark:text-slate-200 dark:hover:bg-slate-900"
              aria-label={`Quitar foto ${i + 1}`}
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          </li>
        ))}
        {fotos.length < MAXIMO_FOTOS && (
          <li>
            <label className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-slate-300 p-2 text-center text-xs font-medium text-slate-700 hover:bg-slate-50 has-focus-visible:ring-2 has-focus-visible:ring-marca-600 dark:border-white/20 dark:text-slate-200 dark:hover:bg-white/5 dark:has-focus-visible:ring-amber-400">
              <ImagePlus className="size-6 text-slate-400 dark:text-amber-400" aria-hidden="true" />
              Agregar fotos
              <input
                type="file"
                accept={TIPOS_FOTO.join(',')}
                multiple
                className="sr-only"
                onChange={elegir}
              />
            </label>
          </li>
        )}
      </ul>
      {error && (
        <p className="mt-1 text-sm text-alerta-700 dark:text-red-300" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
