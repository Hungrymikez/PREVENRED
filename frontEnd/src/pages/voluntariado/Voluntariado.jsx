import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { HandHeart, Phone } from 'lucide-react'
import { useState } from 'react'
import { mensajeDeError } from '@/api/client'
import {
  ESTADOS_ASIGNACION,
  HABILIDADES,
  inscribirVoluntario,
  listarMisAsignaciones,
  obtenerMiPerfil,
} from '@/api/voluntariado'
import { SelectorUbicacion } from '@/components/mapa/SelectorUbicacion'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { useAuth } from '@/hooks/useAuth'
import { formatearFecha } from '@/utils/fechas'

const COLOR_ASIGNACION = {
  ASIGNADO: 'ambar',
  EN_CAMINO: 'azul',
  COMPLETADO: 'verde',
  CANCELADO: 'gris',
}

/**
 * CU-44 Inscribirse como voluntario · CU-38 Consultar mis asignaciones.
 * Si la persona ya está inscrita ve su perfil (y puede actualizarlo) y sus misiones.
 */
export default function Voluntariado() {
  const perfil = useQuery({ queryKey: ['voluntariado', 'perfil'], queryFn: obtenerMiPerfil })
  const [editando, setEditando] = useState(false)

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Voluntariado</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Ofrece tus habilidades para apoyar a la comunidad en emergencias y consulta las misiones que
        te asignen.
      </p>

      <section className="mt-5" aria-labelledby="titulo-perfil">
        {perfil.isPending ? (
          <Cargando texto="Cargando tu perfil…" />
        ) : perfil.error ? (
          <ErrorAlCargar error={perfil.error} />
        ) : perfil.data && !editando ? (
          <Perfil perfil={perfil.data} onEditar={() => setEditando(true)} />
        ) : (
          <Inscripcion
            perfil={perfil.data}
            onTerminar={() => setEditando(false)}
            onCancelar={perfil.data ? () => setEditando(false) : undefined}
          />
        )}
      </section>

      {perfil.data && <MisAsignaciones />}
    </div>
  )
}

function Perfil({ perfil, onEditar }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2
            id="titulo-perfil"
            className="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-white"
          >
            <HandHeart className="size-5 text-marca-600 dark:text-amber-400" aria-hidden="true" />
            Estás inscrito como voluntario
          </h2>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{perfil.full_name}</p>
          <p className="mt-0.5 flex items-center gap-1 text-sm text-slate-600 dark:text-slate-300">
            <Phone className="size-3.5" aria-hidden="true" />
            {perfil.phone_number}
          </p>
        </div>
        <Etiqueta color={perfil.is_available ? 'verde' : 'gris'}>
          {perfil.is_available ? 'Disponible' : 'No disponible'}
        </Etiqueta>
      </div>
      <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Tus habilidades">
        {perfil.skills.map((h) => (
          <li key={h}>
            <Etiqueta color="azul">{HABILIDADES[h] ?? h}</Etiqueta>
          </li>
        ))}
      </ul>
      <Boton type="button" variante="secundario" className="mt-4" onClick={onEditar}>
        Actualizar mis datos
      </Boton>
    </div>
  )
}

function Inscripcion({ perfil, onTerminar, onCancelar }) {
  const { usuario } = useAuth()
  const queryClient = useQueryClient()
  const [nombre, setNombre] = useState(perfil?.full_name ?? usuario?.full_name ?? '')
  const [telefono, setTelefono] = useState(perfil?.phone_number ?? '')
  const [habilidades, setHabilidades] = useState(perfil?.skills ?? [])
  const [ubicacion, setUbicacion] = useState(perfil ? [perfil.latitude, perfil.longitude] : null)
  const [errores, setErrores] = useState({})

  const inscripcion = useMutation({
    mutationFn: () => inscribirVoluntario({ nombre, telefono, habilidades, ubicacion }),
    onSuccess: (data) => {
      queryClient.setQueryData(['voluntariado', 'perfil'], data)
      onTerminar()
    },
  })

  function alternar(habilidad) {
    setHabilidades((actuales) =>
      actuales.includes(habilidad)
        ? actuales.filter((h) => h !== habilidad)
        : [...actuales, habilidad],
    )
  }

  function enviar(e) {
    e.preventDefault()
    const encontrados = {}
    if (nombre.trim().length < 3) encontrados.nombre = 'Escribe tu nombre completo.'
    if (!/^\+?[\d\s-]{7,}$/.test(telefono.trim()))
      encontrados.telefono = 'Escribe un teléfono de contacto válido (mínimo 7 dígitos).'
    if (habilidades.length === 0) encontrados.habilidades = 'Elige al menos una habilidad.'
    if (!ubicacion) encontrados.ubicacion = 'Marca desde dónde puedes apoyar.'
    setErrores(encontrados)
    if (Object.keys(encontrados).length === 0) inscripcion.mutate()
  }

  return (
    <form
      onSubmit={enviar}
      noValidate
      className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
    >
      <h2 id="titulo-perfil" className="font-semibold text-slate-900 dark:text-white">
        {perfil ? 'Actualiza tus datos de voluntario' : 'Inscríbete como voluntario'}
      </h2>
      {inscripcion.error && <Alerta tipo="error">{mensajeDeError(inscripcion.error)}</Alerta>}
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo
          etiqueta="Nombre completo"
          maxLength={120}
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          error={errores.nombre}
        />
        <Campo
          etiqueta="Teléfono de contacto"
          type="tel"
          inputMode="tel"
          placeholder="Ej.: 3101234567"
          maxLength={20}
          value={telefono}
          onChange={(e) => setTelefono(e.target.value)}
          error={errores.telefono}
        />
      </div>
      <fieldset>
        <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-200">
          Habilidades
        </legend>
        <div className="grid gap-2 sm:grid-cols-2">
          {Object.entries(HABILIDADES).map(([valor, nombreHabilidad]) => (
            <label
              key={valor}
              className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 has-checked:border-marca-600 has-checked:bg-marca-50 dark:border-white/10 dark:text-slate-200 dark:has-checked:border-amber-400 dark:has-checked:bg-amber-400/10"
            >
              <input
                type="checkbox"
                checked={habilidades.includes(valor)}
                onChange={() => alternar(valor)}
                className="size-4 accent-marca-600 dark:accent-amber-400"
              />
              {nombreHabilidad}
            </label>
          ))}
        </div>
        {errores.habilidades && (
          <p className="mt-1 text-sm text-alerta-700 dark:text-red-300">{errores.habilidades}</p>
        )}
      </fieldset>
      <fieldset>
        <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-200">
          ¿Desde dónde puedes apoyar?
        </legend>
        <SelectorUbicacion valor={ubicacion} onCambiar={setUbicacion} error={errores.ubicacion} />
      </fieldset>
      <div className="flex flex-wrap gap-2">
        <Boton type="submit" cargando={inscripcion.isPending}>
          {perfil ? 'Guardar cambios' : 'Inscribirme'}
        </Boton>
        {onCancelar && (
          <Boton type="button" variante="secundario" onClick={onCancelar}>
            Cancelar
          </Boton>
        )}
      </div>
    </form>
  )
}

function MisAsignaciones() {
  const {
    data: asignaciones = [],
    isPending,
    error,
  } = useQuery({ queryKey: ['voluntariado', 'asignaciones'], queryFn: listarMisAsignaciones })

  return (
    <section className="mt-8" aria-labelledby="titulo-asignaciones">
      <h2 id="titulo-asignaciones" className="text-lg font-semibold text-slate-900 dark:text-white">
        Mis asignaciones
      </h2>
      <div className="mt-3">
        {isPending ? (
          <Cargando texto="Cargando asignaciones…" />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : asignaciones.length === 0 ? (
          <SinResultados titulo="Sin misiones por ahora">
            Cuando un coordinador te asigne una misión, aparecerá aquí.
          </SinResultados>
        ) : (
          <ul className="space-y-3">
            {asignaciones.map((a) => (
              <li
                key={a.id}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="font-medium text-slate-900 dark:text-white">{a.task_description}</p>
                  <Etiqueta color={COLOR_ASIGNACION[a.status] ?? 'gris'}>
                    {ESTADOS_ASIGNACION[a.status] ?? a.status}
                  </Etiqueta>
                </div>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Asignada: {formatearFecha(a.created_at)} · Caso{' '}
                  <span className="font-mono">{a.incident_id.slice(-6).toUpperCase()}</span>
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
