import { useId } from 'react'

/**
 * Campo de formulario con etiqueta y mensaje de error.
 * Funciona con React Hook Form: <Campo etiqueta="Correo" error={errors.email?.message} {...register('email')} />
 * - como="select": lista desplegable (las <option> van como hijos)
 * - como="textarea": texto largo
 */
export function Campo({
  etiqueta,
  error,
  ayuda,
  como = 'input',
  className = '',
  ref,
  children,
  ...props
}) {
  const id = useId()
  const idMensaje = `${id}-mensaje`
  const Elemento = como

  return (
    <div className={className}>
      <label
        htmlFor={id}
        className="mb-1 block text-sm font-medium text-slate-800 dark:text-slate-200"
      >
        {etiqueta}
      </label>
      <Elemento
        id={id}
        ref={ref}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error || ayuda ? idMensaje : undefined}
        className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:outline-none dark:bg-white/10 dark:text-white dark:[color-scheme:dark] dark:placeholder:text-slate-400 ${
          error
            ? 'border-alerta-600 focus:ring-alerta-600 dark:border-red-400 dark:focus:ring-red-400'
            : 'border-slate-300 focus:border-marca-600 focus:ring-marca-600 dark:border-white/20 dark:focus:border-amber-400 dark:focus:ring-amber-400'
        }`}
        {...props}
      >
        {children}
      </Elemento>
      {error ? (
        <p id={idMensaje} className="mt-1 text-sm text-alerta-700 dark:text-red-300">
          {error}
        </p>
      ) : (
        ayuda && (
          <p id={idMensaje} className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {ayuda}
          </p>
        )
      )}
    </div>
  )
}
