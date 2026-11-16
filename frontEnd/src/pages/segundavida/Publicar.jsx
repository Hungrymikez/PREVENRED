import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { CATEGORIAS, CONDICIONES, MODALIDADES, publicar, UNIDADES } from '@/api/segundavida'
import { textoDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Volver } from '@/components/ui/Volver'
import { useAuth } from '@/hooks/useAuth'
import { NOMBRES_ZONAS } from '@/utils/zonas'
import { esquemaPublicacion } from './esquema'
import { SelectorFotos } from './SelectorFotos'

/** CU-11 · Publicar material. Las fotos se suben primero (CU-47) y viajan en media_urls. */
export default function Publicar() {
  const { usuario } = useAuth()
  const navegar = useNavigate()
  const queryClient = useQueryClient()
  const [fotos, setFotos] = useState([])

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(esquemaPublicacion),
    defaultValues: {
      offerType: 'VENTA',
      title: '',
      description: '',
      category: '',
      condition: '',
      quantity: 1,
      unit: UNIDADES[0],
      price: '',
      // Por defecto, el barrio de su cuenta si está en la lista.
      zona: NOMBRES_ZONAS.includes(usuario.neighborhood) ? usuario.neighborhood : '',
    },
  })
  const modalidad = useWatch({ control, name: 'offerType' })

  const publicacion = useMutation({
    mutationFn: (datos) => publicar(datos, fotos),
    onSuccess: (nueva) => {
      queryClient.invalidateQueries({ queryKey: ['publicaciones'] }) // la lista se recarga
      navegar(`/segundavida/${nueva.id}`)
    },
  })

  return (
    <div className="mx-auto max-w-2xl">
      <Volver a="/segundavida">Volver a SegundaVida</Volver>
      <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
        Publicar en SegundaVida
      </h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Dale una segunda vida a lo que te sobró. Solo mostramos tu barrio, nunca tu dirección.
      </p>

      <form
        onSubmit={handleSubmit((datos) => publicacion.mutate(datos))}
        noValidate
        className="mt-6 space-y-4 rounded-2xl bg-white p-6 shadow-sm dark:bg-slate-900"
      >
        {publicacion.error && <Alerta tipo="error">{textoDeError(publicacion.error)}</Alerta>}

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-100">
            ¿Qué quieres hacer?
          </legend>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(MODALIDADES).map(([valor, { nombre }]) => (
              <label
                key={valor}
                className="cursor-pointer rounded-lg border border-slate-300 p-2 text-center text-sm font-medium has-checked:border-marca-600 has-checked:bg-marca-50 has-focus-visible:ring-2 has-focus-visible:ring-marca-600 dark:border-white/20 dark:has-checked:border-amber-400 dark:has-checked:bg-amber-400/10 dark:has-focus-visible:ring-amber-400"
              >
                <input type="radio" value={valor} className="sr-only" {...register('offerType')} />
                {nombre}
              </label>
            ))}
          </div>
        </fieldset>

        <Campo
          etiqueta="Título"
          placeholder="Ej.: Tejas de zinc"
          error={errors.title?.message}
          {...register('title')}
        />
        <Campo
          como="textarea"
          rows={4}
          etiqueta="Descripción"
          placeholder="Cuenta cómo está, medidas, por qué lo publicas…"
          error={errors.description?.message}
          {...register('description')}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Campo
            como="select"
            etiqueta="Categoría"
            error={errors.category?.message}
            {...register('category')}
          >
            <option value="">Elige…</option>
            {Object.entries(CATEGORIAS).map(([valor, nombre]) => (
              <option key={valor} value={valor}>
                {nombre}
              </option>
            ))}
          </Campo>
          <Campo
            como="select"
            etiqueta="Estado"
            error={errors.condition?.message}
            {...register('condition')}
          >
            <option value="">Elige…</option>
            {Object.entries(CONDICIONES).map(([valor, nombre]) => (
              <option key={valor} value={valor}>
                {nombre}
              </option>
            ))}
          </Campo>
          <Campo
            etiqueta="Cantidad"
            type="number"
            min="0"
            step="any"
            inputMode="decimal"
            error={errors.quantity?.message}
            {...register('quantity')}
          />
          <Campo como="select" etiqueta="Unidad" error={errors.unit?.message} {...register('unit')}>
            {UNIDADES.map((u) => (
              <option key={u}>{u}</option>
            ))}
          </Campo>
          {modalidad !== 'DONACION' && (
            <Campo
              etiqueta={modalidad === 'ALQUILER' ? 'Costo por día (COP)' : 'Precio (COP)'}
              type="number"
              min="0"
              step="1000"
              inputMode="numeric"
              error={errors.price?.message}
              {...register('price')}
            />
          )}
          <Campo como="select" etiqueta="Barrio" error={errors.zona?.message} {...register('zona')}>
            <option value="">Elige…</option>
            {NOMBRES_ZONAS.map((z) => (
              <option key={z}>{z}</option>
            ))}
          </Campo>
        </div>

        <SelectorFotos fotos={fotos} onCambiar={setFotos} />

        <Boton type="submit" cargando={publicacion.isPending} className="w-full">
          Publicar
        </Boton>
      </form>
    </div>
  )
}
