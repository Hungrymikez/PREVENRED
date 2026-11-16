import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { mensajeDeError } from '@/api/client'
import { HABITABILIDAD, NIVELES_DANO, registrarInspeccion } from '@/api/inspecciones'
import { SelectorUbicacion } from '@/components/mapa/SelectorUbicacion'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Volver } from '@/components/ui/Volver'

/** Lee ?lat=..&lon=.. (cuando se llega desde un caso de la bandeja). */
function ubicacionInicial(params) {
  const lat = Number.parseFloat(params.get('lat'))
  const lon = Number.parseFloat(params.get('lon'))
  return Number.isFinite(lat) && Number.isFinite(lon) ? [lat, lon] : null
}

function validar(f) {
  const errores = {}
  const residentes = Number(f.residentes)
  if (f.direccion.trim().length < 5) errores.direccion = 'Escribe la dirección completa.'
  if (f.barrio.trim().length < 2) errores.barrio = 'Indica el barrio o comuna.'
  if (f.residentes === '' || !Number.isInteger(residentes) || residentes < 0)
    errores.residentes = 'Indica cuántas personas viven allí (0 o más).'
  if (!f.nivelDano) errores.nivelDano = 'Elige el nivel de daño.'
  if (!f.habitabilidad) errores.habitabilidad = 'Elige el resultado de habitabilidad.'
  if (!f.ubicacion) errores.ubicacion = 'Marca la ubicación del inmueble.'
  return errores
}

const FORM_VACIO = {
  direccion: '',
  barrio: '',
  residentes: '',
  nivelDano: '',
  habitabilidad: '',
  notas: '',
}

/**
 * CU-34 Censar inmueble · CU-36 Registrar inspección de habitabilidad (inspector o admin).
 * Puede abrirse desde un caso de la bandeja: /inspecciones/nueva?caso=<id>&lat=..&lon=..
 * (la ubicación llega marcada y la referencia al caso se guarda en los hallazgos).
 */
export default function NuevaInspeccion() {
  const [params] = useSearchParams()
  const caso = params.get('caso') ?? ''
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ ...FORM_VACIO, ubicacion: ubicacionInicial(params) })
  const [errores, setErrores] = useState({})

  const registro = useMutation({
    mutationFn: () => registrarInspeccion({ ...form, caso: caso || undefined }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inspecciones'] }),
  })

  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }))

  function enviar(e) {
    e.preventDefault()
    const encontrados = validar(form)
    setErrores(encontrados)
    if (Object.keys(encontrados).length === 0) registro.mutate()
  }

  if (registro.isSuccess) {
    const i = registro.data
    return (
      <div className="mx-auto max-w-xl space-y-4">
        <Alerta tipo="exito">
          Inspección registrada: {i.property_address} ·{' '}
          {HABITABILIDAD[i.habitability] ?? i.habitability}.
        </Alerta>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/inspecciones"
            className="rounded-lg bg-marca-600 px-4 py-2.5 font-medium text-white hover:bg-marca-700 dark:bg-amber-500 dark:text-slate-950 dark:hover:bg-amber-400"
          >
            Ver inspecciones
          </Link>
          <Boton
            type="button"
            variante="secundario"
            onClick={() => {
              registro.reset()
              setForm((f) => ({ ...FORM_VACIO, ubicacion: f.ubicacion }))
            }}
          >
            Registrar otra
          </Boton>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-xl">
      <Volver a="/inspecciones">Inspecciones</Volver>
      <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">Nueva inspección</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Censa el inmueble y registra el resultado de habitabilidad.
      </p>
      {caso && (
        <div className="mt-3">
          <Alerta tipo="info">Inspección relacionada con el caso {caso}.</Alerta>
        </div>
      )}

      <form
        onSubmit={enviar}
        noValidate
        className="mt-5 space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
      >
        {registro.error && <Alerta tipo="error">{mensajeDeError(registro.error)}</Alerta>}
        <Campo
          etiqueta="Dirección del inmueble"
          placeholder="Ej.: Calle 14 # 9-30"
          maxLength={200}
          value={form.direccion}
          onChange={cambiar('direccion')}
          error={errores.direccion}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo
            etiqueta="Barrio o comuna"
            placeholder="Ej.: Cuba"
            maxLength={100}
            value={form.barrio}
            onChange={cambiar('barrio')}
            error={errores.barrio}
          />
          <Campo
            etiqueta="Número de residentes"
            type="number"
            min="0"
            inputMode="numeric"
            value={form.residentes}
            onChange={cambiar('residentes')}
            error={errores.residentes}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo
            como="select"
            etiqueta="Nivel de daño"
            value={form.nivelDano}
            onChange={cambiar('nivelDano')}
            error={errores.nivelDano}
          >
            <option value="">Elige…</option>
            {Object.entries(NIVELES_DANO).map(([valor, nombre]) => (
              <option key={valor} value={valor}>
                {nombre}
              </option>
            ))}
          </Campo>
          <Campo
            como="select"
            etiqueta="Habitabilidad"
            value={form.habitabilidad}
            onChange={cambiar('habitabilidad')}
            error={errores.habitabilidad}
          >
            <option value="">Elige…</option>
            {Object.entries(HABITABILIDAD).map(([valor, nombre]) => (
              <option key={valor} value={valor}>
                {nombre}
              </option>
            ))}
          </Campo>
        </div>
        <Campo
          como="textarea"
          rows={3}
          etiqueta="Hallazgos técnicos (opcional)"
          placeholder="Ej.: Grietas diagonales en muro de carga"
          maxLength={2000}
          value={form.notas}
          onChange={cambiar('notas')}
        />
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-200">
            Ubicación del inmueble
          </legend>
          <SelectorUbicacion
            valor={form.ubicacion}
            onCambiar={(ubicacion) => setForm((f) => ({ ...f, ubicacion }))}
            error={errores.ubicacion}
          />
        </fieldset>
        <Boton type="submit" cargando={registro.isPending} className="w-full">
          Registrar inspección
        </Boton>
      </form>
    </div>
  )
}
