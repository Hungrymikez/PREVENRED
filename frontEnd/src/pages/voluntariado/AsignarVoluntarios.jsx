import { useMutation, useQuery } from '@tanstack/react-query'
import { MapPin, Phone, UserRound } from 'lucide-react'
import { useState } from 'react'
import { listarCasos, TIPOS_CASO } from '@/api/casos'
import { mensajeDeError } from '@/api/client'
import { asignarVoluntario, HABILIDADES, listarVoluntarios } from '@/api/voluntariado'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Cargando, ErrorAlCargar, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'

/**
 * CU-43 · Asignar voluntarios (administrador o inspector).
 * Lista los voluntarios disponibles y asigna a cada uno una tarea sobre un caso abierto.
 */
export default function AsignarVoluntarios() {
  const [filtro, setFiltro] = useState('')
  const voluntarios = useQuery({ queryKey: ['voluntarios'], queryFn: listarVoluntarios })
  // Casos abiertos a los que se puede enviar apoyo (los resueltos no se ofrecen).
  const casos = useQuery({
    queryKey: ['casos', 'abiertos'],
    queryFn: () => listarCasos(),
    select: (lista) => lista.filter((c) => c.status !== 'RESUELTO'),
  })

  const lista = (voluntarios.data ?? []).filter((v) => !filtro || v.skills.includes(filtro))

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Asignar voluntarios</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Voluntarios disponibles para apoyar la atención de los casos reportados.
      </p>

      <div className="mt-5 max-w-xs">
        <Campo
          como="select"
          etiqueta="Filtrar por habilidad"
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
        >
          <option value="">Todas las habilidades</option>
          {Object.entries(HABILIDADES).map(([valor, nombre]) => (
            <option key={valor} value={valor}>
              {nombre}
            </option>
          ))}
        </Campo>
      </div>

      <div className="mt-5">
        {voluntarios.isPending ? (
          <Cargando texto="Cargando voluntarios…" />
        ) : voluntarios.error ? (
          <ErrorAlCargar error={voluntarios.error} />
        ) : lista.length === 0 ? (
          <SinResultados titulo="No hay voluntarios disponibles">
            {filtro
              ? `Nadie disponible con la habilidad «${HABILIDADES[filtro]}».`
              : 'Cuando alguien se inscriba como voluntario aparecerá aquí.'}
          </SinResultados>
        ) : (
          <ul className="space-y-3">
            {lista.map((v) => (
              <li key={v.id}>
                <TarjetaVoluntario voluntario={v} casos={casos} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}

function TarjetaVoluntario({ voluntario: v, casos }) {
  const [asignando, setAsignando] = useState(false)
  const [ultima, setUltima] = useState(null)

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-white">
            <UserRound className="size-4 text-marca-600 dark:text-amber-400" aria-hidden="true" />
            {v.full_name}
          </h2>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
            <span className="inline-flex items-center gap-1">
              <Phone className="size-3.5" aria-hidden="true" />
              {v.phone_number}
            </span>
            <a
              href={`https://www.openstreetmap.org/?mlat=${v.latitude}&mlon=${v.longitude}#map=15/${v.latitude}/${v.longitude}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 font-medium text-marca-700 hover:underline dark:text-amber-400"
            >
              <MapPin className="size-3.5" aria-hidden="true" />
              Ver ubicación
            </a>
          </p>
        </div>
        <Etiqueta color="verde">Disponible</Etiqueta>
      </div>
      <ul className="mt-2 flex flex-wrap gap-1.5" aria-label={`Habilidades de ${v.full_name}`}>
        {v.skills.map((h) => (
          <li key={h}>
            <Etiqueta color="azul">{HABILIDADES[h] ?? h}</Etiqueta>
          </li>
        ))}
      </ul>

      {ultima && !asignando && (
        <div className="mt-3">
          <Alerta tipo="exito">Misión asignada: {ultima.task_description}</Alerta>
        </div>
      )}
      {asignando ? (
        <FormAsignacion
          voluntario={v}
          casos={casos}
          onAsignada={(a) => {
            setUltima(a)
            setAsignando(false)
          }}
          onCancelar={() => setAsignando(false)}
        />
      ) : (
        <Boton type="button" className="mt-3" onClick={() => setAsignando(true)}>
          Asignar misión
        </Boton>
      )}
    </article>
  )
}

function FormAsignacion({ voluntario, casos, onAsignada, onCancelar }) {
  const opciones = casos.data ?? []
  const [elegido, setElegido] = useState('')
  // Si los casos cargan después de abrir el formulario, se toma el primero por defecto.
  const casoId = elegido || opciones[0]?.id || ''
  const [tarea, setTarea] = useState('')
  const [error, setError] = useState('')

  const asignacion = useMutation({
    mutationFn: () => asignarVoluntario({ voluntarioId: voluntario.id, casoId, tarea }),
    onSuccess: onAsignada,
  })

  if (casos.isPending) return <Cargando texto="Cargando casos…" />
  if (casos.error) return <ErrorAlCargar error={casos.error} />
  if (opciones.length === 0) {
    return (
      <div className="mt-3 space-y-2">
        <Alerta tipo="info">No hay casos abiertos a los que asignar apoyo.</Alerta>
        <Boton type="button" variante="secundario" onClick={onCancelar}>
          Cerrar
        </Boton>
      </div>
    )
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (tarea.trim().length < 5) {
          setError('Describe la tarea (mínimo 5 caracteres).')
          return
        }
        setError('')
        asignacion.mutate()
      }}
      noValidate
      className="mt-3 space-y-3 rounded-xl bg-slate-50 p-3 dark:bg-white/5"
    >
      {asignacion.error && <Alerta tipo="error">{mensajeDeError(asignacion.error)}</Alerta>}
      <Campo
        como="select"
        etiqueta="Caso"
        value={casoId}
        onChange={(e) => setElegido(e.target.value)}
      >
        {opciones.map((c) => (
          <option key={c.id} value={c.id}>
            {c.case_number} · {TIPOS_CASO[c.incident_type] ?? c.incident_type}
          </option>
        ))}
      </Campo>
      <Campo
        etiqueta="Tarea"
        placeholder="Ej.: Apoyar la evacuación de familias del sector"
        maxLength={500}
        value={tarea}
        onChange={(e) => setTarea(e.target.value)}
        error={error}
      />
      <div className="flex flex-wrap gap-2">
        <Boton type="submit" cargando={asignacion.isPending}>
          Asignar
        </Boton>
        <Boton type="button" variante="secundario" onClick={onCancelar}>
          Cancelar
        </Boton>
      </div>
    </form>
  )
}
