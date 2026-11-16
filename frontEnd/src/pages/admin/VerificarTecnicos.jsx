import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MapPin, Phone } from 'lucide-react'
import { useState } from 'react'
import { mensajeDeError } from '@/api/client'
import { listarPendientes, nombreEspecialidad, verificarTecnico } from '@/api/oficiosya'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Cargando, SinResultados } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { formatearFecha } from '@/utils/fechas'

const CLAVE = ['tecnicos-pendientes']

/**
 * CU-18 · Verificar técnico. El Administrador revisa los perfiles que esperan verificación
 * (los más antiguos primero) y los aprueba o rechaza. Solo los verificados aparecen en
 * OficiosYa (CU-19).
 */
export default function VerificarTecnicos() {
  const [aviso, setAviso] = useState(null)
  const {
    data: pendientes = [],
    isPending,
    error,
  } = useQuery({
    queryKey: CLAVE,
    queryFn: listarPendientes,
  })

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Verificar técnicos</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Perfiles de OficiosYa que esperan revisión. Solo los aprobados aparecen en las búsquedas.
      </p>

      {aviso && (
        <div className="mt-4">
          <Alerta tipo="exito">{aviso}</Alerta>
        </div>
      )}

      <div className="mt-5">
        {isPending ? (
          <Cargando texto="Cargando perfiles…" />
        ) : error ? (
          <Alerta tipo="error">{mensajeDeError(error)}</Alerta>
        ) : pendientes.length === 0 ? (
          <SinResultados titulo="No hay perfiles pendientes">
            Cuando un técnico registre su perfil aparecerá aquí.
          </SinResultados>
        ) : (
          <>
            <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
              {pendientes.length === 1 ? '1 perfil' : `${pendientes.length} perfiles`} · más
              antiguos primero
            </p>
            <ul className="space-y-3">
              {pendientes.map((t) => (
                <li key={t.id}>
                  <TarjetaPendiente tecnico={t} onRevisado={setAviso} />
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </>
  )
}

function TarjetaPendiente({ tecnico: t, onRevisado }) {
  const queryClient = useQueryClient()
  const [confirmarRechazo, setConfirmarRechazo] = useState(false)

  const revision = useMutation({
    mutationFn: (aprobar) => verificarTecnico(t.id, aprobar),
    onSuccess: (_, aprobar) => {
      onRevisado(
        aprobar
          ? `El perfil de ${t.full_name} quedó verificado.`
          : `El perfil de ${t.full_name} fue rechazado.`,
      )
      queryClient.invalidateQueries({ queryKey: CLAVE })
      queryClient.invalidateQueries({ queryKey: ['tecnicos'] })
    },
  })

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold text-slate-900 dark:text-white">{t.full_name}</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Registrado: {formatearFecha(t.created_at)}
          </p>
        </div>
        <Etiqueta color="ambar">Pendiente</Etiqueta>
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        {t.specialties.map((e) => (
          <Etiqueta key={e} color="azul">
            {nombreEspecialidad(e)}
          </Etiqueta>
        ))}
      </div>
      <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-300">
        <span>
          {t.experience_years === 1 ? '1 año' : `${t.experience_years} años`} de experiencia
        </span>
        <span className="inline-flex items-center gap-1">
          <Phone className="size-4" aria-hidden="true" />
          {t.phone_number}
        </span>
        <span className="inline-flex items-center gap-1">
          <MapPin className="size-4" aria-hidden="true" />
          Cerca de {t.zona}
        </span>
      </p>
      {t.bio && <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">{t.bio}</p>}

      {revision.error && (
        <div className="mt-3">
          <Alerta tipo="error">{mensajeDeError(revision.error)}</Alerta>
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {confirmarRechazo ? (
          <>
            <span className="text-sm text-slate-700 dark:text-slate-200">
              ¿Rechazar este perfil?
            </span>
            <Boton
              type="button"
              variante="peligro"
              cargando={revision.isPending}
              onClick={() => revision.mutate(false)}
            >
              Sí, rechazar
            </Boton>
            <Boton type="button" variante="secundario" onClick={() => setConfirmarRechazo(false)}>
              Cancelar
            </Boton>
          </>
        ) : (
          <>
            <Boton
              type="button"
              variante="exito"
              cargando={revision.isPending}
              onClick={() => revision.mutate(true)}
            >
              Aprobar
            </Boton>
            <Boton
              type="button"
              variante="secundario"
              disabled={revision.isPending}
              onClick={() => setConfirmarRechazo(true)}
            >
              Rechazar
            </Boton>
          </>
        )}
      </div>
    </article>
  )
}
