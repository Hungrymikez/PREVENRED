import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Camera, CircleCheck, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { CATEGORIAS_REPORTE, crearReporte } from '@/api/incidentes'
import { SelectorUbicacion } from '@/components/mapa/SelectorUbicacion'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { SinResultados } from '@/components/ui/Estados'
import { Volver } from '@/components/ui/Volver'

const TAMANO_MAXIMO_FOTO_MB = 10
const PASOS = ['¿Qué pasó?', 'Foto y detalles', '¿Dónde es?']
const TIPOS_QUE_EXIGEN_DESCRIPCION = ['OTRO_DANO', 'OTRO_INCIDENTE', 'OTRA_NECESIDAD']

/** CU-29, CU-30 y CU-31: reporte en 3 pasos (RNF-10). */
export default function Reportar() {
  const { categoria } = useParams()
  const config = CATEGORIAS_REPORTE[categoria]
  const queryClient = useQueryClient()

  const [paso, setPaso] = useState(0)
  const [datos, setDatos] = useState({
    type: '',
    quantity: '1',
    description: '',
    foto: null,
    coordenadas: null,
  })
  const [errores, setErrores] = useState({})

  const envio = useMutation({
    mutationFn: () => crearReporte({ categoria, ...datos }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mis-casos'] }),
  })

  if (!config) {
    return <SinResultados titulo="Ese tipo de reporte no existe" />
  }
  if (envio.isSuccess) {
    return <Confirmacion caso={envio.data} />
  }

  const esAyuda = categoria === 'ayuda'

  function cambiar(campo, valor) {
    setDatos((d) => ({ ...d, [campo]: valor }))
    setErrores((e) => ({ ...e, [campo]: undefined }))
  }

  function validar() {
    const e = {}
    if (paso === 0) {
      if (!datos.type) e.type = esAyuda ? 'Elige qué necesitas.' : 'Elige qué pasó.'
      if (esAyuda && !(Number(datos.quantity) >= 1)) e.quantity = 'Indica al menos 1 persona.'
    }
    if (paso === 1 && TIPOS_QUE_EXIGEN_DESCRIPCION.includes(datos.type)) {
      if (datos.description.trim().length < 5)
        e.description = 'Cuéntanos en pocas palabras qué pasa.'
    }
    if (paso === 2 && !datos.coordenadas)
      e.coordenadas = 'Indica dónde es: usa el GPS o toca el mapa.'
    setErrores(e)
    return Object.keys(e).length === 0
  }

  function siguiente(evento) {
    evento.preventDefault()
    if (!validar()) return
    if (paso < PASOS.length - 1) setPaso(paso + 1)
    else envio.mutate()
  }

  return (
    <div className="mx-auto max-w-xl">
      <Volver a="/emergencia">Cambiar tipo de reporte</Volver>
      <h1 className="mt-4 text-2xl font-bold text-slate-900">{config.titulo}</h1>

      <ol className="mt-4 grid grid-cols-3 gap-2" aria-label="Pasos del reporte">
        {PASOS.map((nombre, i) => (
          <li
            key={nombre}
            aria-current={i === paso ? 'step' : undefined}
            className={`border-t-4 pt-1 text-xs font-medium ${
              i <= paso ? 'border-alerta-600 text-slate-900' : 'border-slate-200 text-slate-400'
            }`}
          >
            Paso {i + 1}
            <span className="block">{nombre}</span>
          </li>
        ))}
      </ol>

      <form
        onSubmit={siguiente}
        noValidate
        className="mt-6 space-y-5 rounded-2xl bg-white p-5 shadow-sm"
      >
        {paso === 0 && (
          <>
            <fieldset>
              <legend className="font-semibold text-slate-900">
                {esAyuda ? '¿Qué necesitas?' : '¿Qué pasó?'}
              </legend>
              <div className="mt-3 grid gap-2">
                {Object.entries(config.tipos).map(([valor, nombre]) => (
                  <label
                    key={valor}
                    className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-300 p-3 font-medium text-slate-900 has-checked:border-alerta-600 has-checked:bg-alerta-50 has-focus-visible:ring-2 has-focus-visible:ring-alerta-600"
                  >
                    <input
                      type="radio"
                      name="type"
                      value={valor}
                      checked={datos.type === valor}
                      onChange={() => cambiar('type', valor)}
                      className="size-4 accent-alerta-600"
                    />
                    {nombre}
                  </label>
                ))}
              </div>
              {errores.type && <p className="mt-1 text-sm text-alerta-700">{errores.type}</p>}
            </fieldset>
            {esAyuda && (
              <Campo
                etiqueta="¿Para cuántas personas?"
                type="number"
                min="1"
                inputMode="numeric"
                value={datos.quantity}
                onChange={(e) => cambiar('quantity', e.target.value)}
                error={errores.quantity}
              />
            )}
            {datos.type === 'APOYO_EMOCIONAL' && (
              <Alerta tipo="info">
                Si necesitas hablar con alguien ya, entra a{' '}
                <Link to="/mente-resiliente" className="font-semibold underline">
                  Apoyo
                </Link>
                . Si alguien está en peligro, llama al 123.
              </Alerta>
            )}
          </>
        )}

        {paso === 1 && (
          <>
            <SelectorFoto foto={datos.foto} onCambiar={(f) => cambiar('foto', f)} />
            <Campo
              como="textarea"
              rows={3}
              maxLength={500}
              etiqueta={
                TIPOS_QUE_EXIGEN_DESCRIPCION.includes(datos.type)
                  ? 'Describe lo que pasa'
                  : 'Describe lo que pasa (opcional)'
              }
              placeholder={
                esAyuda
                  ? 'Ej.: somos una familia con dos niños'
                  : 'Ej.: el muro de la cocina se agrietó'
              }
              value={datos.description}
              onChange={(e) => cambiar('description', e.target.value)}
              error={errores.description}
            />
          </>
        )}

        {paso === 2 && (
          <fieldset>
            <legend className="mb-3 font-semibold text-slate-900">¿Dónde es?</legend>
            <SelectorUbicacion
              valor={datos.coordenadas}
              onCambiar={(c) => cambiar('coordenadas', c)}
              error={errores.coordenadas}
            />
          </fieldset>
        )}

        {envio.error && (
          <Alerta tipo="error">
            No se pudo enviar el reporte. Tus datos siguen aquí: intenta de nuevo.
          </Alerta>
        )}

        <div className="flex gap-2">
          {paso > 0 && (
            <Boton type="button" variante="secundario" onClick={() => setPaso(paso - 1)}>
              Atrás
            </Boton>
          )}
          <Boton type="submit" variante="peligro" cargando={envio.isPending} className="flex-1">
            {paso < PASOS.length - 1 ? 'Siguiente' : 'Enviar reporte'}
          </Boton>
        </div>
      </form>
    </div>
  )
}

/**
 * Foto opcional (O-13). Por ahora solo se muestra la vista previa:
 * la subida real llega con el servicio de archivos (CU-47).
 */
function SelectorFoto({ foto, onCambiar }) {
  const [error, setError] = useState('')
  const vistaPrevia = useMemo(() => (foto ? URL.createObjectURL(foto) : null), [foto])
  // Libera la memoria de la vista previa al cambiar o quitar la foto.
  useEffect(() => () => vistaPrevia && URL.revokeObjectURL(vistaPrevia), [vistaPrevia])

  function elegir(e) {
    const archivo = e.target.files?.[0]
    e.target.value = ''
    if (!archivo) return
    if (!archivo.type.startsWith('image/')) return setError('El archivo debe ser una imagen.')
    if (archivo.size > TAMANO_MAXIMO_FOTO_MB * 1024 * 1024) {
      return setError(`La foto no puede pesar más de ${TAMANO_MAXIMO_FOTO_MB} MB.`)
    }
    setError('')
    onCambiar(archivo)
  }

  return (
    <div>
      <p className="mb-2 font-semibold text-slate-900">Foto (opcional)</p>
      {vistaPrevia ? (
        <div className="relative">
          <img
            src={vistaPrevia}
            alt="Foto del reporte"
            className="h-48 w-full rounded-xl object-cover"
          />
          <button
            type="button"
            onClick={() => onCambiar(null)}
            className="absolute top-2 right-2 rounded-full bg-white/90 p-1.5 text-slate-700 shadow hover:bg-white"
            aria-label="Quitar foto"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
      ) : (
        <label className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed border-slate-300 p-6 text-center text-sm font-medium text-slate-700 hover:bg-slate-50 has-focus-visible:ring-2 has-focus-visible:ring-alerta-600">
          <Camera className="size-8 text-slate-400" aria-hidden="true" />
          Tomar o elegir una foto
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="sr-only"
            onChange={elegir}
          />
        </label>
      )}
      {error && <p className="mt-1 text-sm text-alerta-700">{error}</p>}
    </div>
  )
}

function Confirmacion({ caso }) {
  return (
    <div className="mx-auto max-w-xl rounded-2xl bg-white p-6 text-center shadow-sm" role="status">
      <CircleCheck className="mx-auto size-12 text-green-600" aria-hidden="true" />
      <h1 className="mt-3 text-2xl font-bold text-slate-900">Reporte enviado</h1>
      <p className="mt-1 text-slate-600">Guarda este número para hacerle seguimiento:</p>
      <p className="mt-3 rounded-xl bg-slate-100 py-3 font-mono text-2xl font-bold tracking-wider text-slate-900">
        {caso.caseId}
      </p>
      {caso.categoria === 'vivienda' && (
        <p className="mt-4 text-sm text-slate-600">
          Este reporte no es una evaluación oficial de tu vivienda. Un inspector autorizado la
          revisará.
        </p>
      )}
      <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-center">
        <Link
          to={`/emergencia/casos/${caso.caseId}`}
          className="rounded-lg bg-marca-600 px-4 py-2.5 font-medium text-white hover:bg-marca-700"
        >
          Ver mi caso
        </Link>
        <Link
          to="/emergencia"
          className="rounded-lg border border-slate-300 px-4 py-2.5 font-medium text-slate-800 hover:bg-slate-50"
        >
          Hacer otro reporte
        </Link>
      </div>
    </div>
  )
}
