import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Package } from 'lucide-react'
import { useState } from 'react'
import { mensajeDeError } from '@/api/client'
import {
  CATEGORIAS_AYUDA,
  ESTADOS_AYUDA,
  formatearCantidad,
  listarMisOfertas,
  ofrecerAyuda,
} from '@/api/donaciones'
import { SelectorUbicacion } from '@/components/mapa/SelectorUbicacion'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { formatearFecha } from '@/utils/fechas'

const COLOR_ESTADO = {
  PENDIENTE: 'verde',
  EMPAREJADO: 'azul',
  ENTREGADO: 'gris',
  CANCELADO: 'gris',
}

const UNIDADES_SUGERIDAS = ['unidades', 'kg', 'litros', 'paquetes', 'cajas', 'kits']

const FORM_VACIO = { titulo: '', categoria: '', cantidad: '', unidad: 'unidades' }

/**
 * CU-33 · Ofrecer ayuda (donar). La persona registra lo que puede donar y ve sus ofertas:
 * cuánto sigue disponible y cuándo la administración la empareja con una necesidad (CU-42).
 */
export default function Donar() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState(FORM_VACIO)
  const [ubicacion, setUbicacion] = useState(null)
  const [errores, setErrores] = useState({})

  const oferta = useMutation({
    mutationFn: () => ofrecerAyuda({ ...form, ubicacion }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donaciones', 'mias'] })
      setForm(FORM_VACIO)
      setErrores({})
    },
  })

  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }))

  function enviar(e) {
    e.preventDefault()
    const encontrados = {}
    if (form.titulo.trim().length < 3)
      encontrados.titulo = 'Describe lo que donas (mínimo 3 caracteres).'
    if (!form.categoria) encontrados.categoria = 'Elige una categoría.'
    if (!(Number(form.cantidad) > 0)) encontrados.cantidad = 'La cantidad debe ser mayor a 0.'
    if (!form.unidad.trim()) encontrados.unidad = 'Indica la unidad.'
    if (!ubicacion) encontrados.ubicacion = 'Marca dónde se puede recoger la donación.'
    setErrores(encontrados)
    if (Object.keys(encontrados).length === 0) oferta.mutate()
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Donar</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Ofrece alimentos, agua, ropa u otros recursos. La administración los empareja con las
        necesidades más urgentes y cercanas.
      </p>

      <form
        onSubmit={enviar}
        noValidate
        className="mt-5 space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
      >
        <h2 className="font-semibold text-slate-900 dark:text-white">Nueva oferta de ayuda</h2>
        {oferta.isSuccess && (
          <Alerta tipo="exito">
            ¡Gracias! Registramos tu oferta «{oferta.data.title}». Te avisaremos cuando se empareje.
          </Alerta>
        )}
        {oferta.error && <Alerta tipo="error">{mensajeDeError(oferta.error)}</Alerta>}
        <Campo
          etiqueta="¿Qué donas?"
          placeholder="Ej.: Agua embotellada"
          maxLength={120}
          value={form.titulo}
          onChange={cambiar('titulo')}
          error={errores.titulo}
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Campo
            como="select"
            etiqueta="Categoría"
            value={form.categoria}
            onChange={cambiar('categoria')}
            error={errores.categoria}
          >
            <option value="">Elige…</option>
            {Object.entries(CATEGORIAS_AYUDA).map(([valor, nombre]) => (
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
            value={form.cantidad}
            onChange={cambiar('cantidad')}
            error={errores.cantidad}
          />
          <Campo
            etiqueta="Unidad"
            list="unidades-donacion"
            maxLength={30}
            value={form.unidad}
            onChange={cambiar('unidad')}
            error={errores.unidad}
            ayuda="Debe coincidir con la de la necesidad."
          />
          <datalist id="unidades-donacion">
            {UNIDADES_SUGERIDAS.map((u) => (
              <option key={u} value={u} />
            ))}
          </datalist>
        </div>
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-200">
            ¿Dónde se puede recoger?
          </legend>
          <SelectorUbicacion valor={ubicacion} onCambiar={setUbicacion} error={errores.ubicacion} />
        </fieldset>
        <Boton type="submit" cargando={oferta.isPending} className="w-full">
          Ofrecer ayuda
        </Boton>
      </form>

      <MisOfertas />
    </div>
  )
}

function MisOfertas() {
  const {
    data: ofertas = [],
    isPending,
    error,
  } = useQuery({ queryKey: ['donaciones', 'mias'], queryFn: listarMisOfertas })

  return (
    <section className="mt-8" aria-labelledby="titulo-mis-ofertas">
      <h2 id="titulo-mis-ofertas" className="text-lg font-semibold text-slate-900 dark:text-white">
        Mis ofertas
      </h2>
      <div className="mt-3">
        {isPending ? (
          <Cargando texto="Cargando tus ofertas…" />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : ofertas.length === 0 ? (
          <SinResultados titulo="Aún no has ofrecido ayuda">
            Tus ofertas aparecerán aquí con su estado.
          </SinResultados>
        ) : (
          <ul className="space-y-3">
            {ofertas.map((o) => (
              <li
                key={o.id}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="flex items-center gap-1.5 font-medium text-slate-900 dark:text-white">
                      <Package
                        className="size-4 text-marca-600 dark:text-amber-400"
                        aria-hidden="true"
                      />
                      {o.title}
                    </p>
                    <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
                      {CATEGORIAS_AYUDA[o.category] ?? o.category} ·{' '}
                      {formatearCantidad(o.quantity, o.unit)}
                    </p>
                  </div>
                  <Etiqueta color={COLOR_ESTADO[o.status] ?? 'gris'}>
                    {ESTADOS_AYUDA[o.status] ?? o.status}
                  </Etiqueta>
                </div>
                <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                  Ofrecida: {formatearFecha(o.created_at)}
                  {o.available_quantity != null &&
                    o.available_quantity < o.quantity &&
                    ` · Quedan ${formatearCantidad(o.available_quantity, o.unit)} disponibles`}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
