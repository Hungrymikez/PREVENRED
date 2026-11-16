import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MapPin, Phone } from 'lucide-react'
import { useState } from 'react'
import { mensajeDeError } from '@/api/client'
import {
  ESPECIALIDADES,
  guardarMiPerfil,
  nombreEspecialidad,
  obtenerMiPerfil,
} from '@/api/oficiosya'
import { SelectorUbicacion } from '@/components/mapa/SelectorUbicacion'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { Cargando } from '@/components/ui/Estados'
import { Etiqueta } from '@/components/ui/Etiqueta'
import { useAuth } from '@/hooks/useAuth'
import { EstadoVerificacion } from './EstadoVerificacion'
import { Valoracion } from './Valoracion'

const CLAVE = ['mi-perfil-tecnico']

const AVISO_ESTADO = {
  PENDIENTE:
    'Un administrador revisará tu perfil. Mientras tanto no aparecerás en las búsquedas de OficiosYa.',
  VERIFICADO: 'Tu perfil está verificado: los ciudadanos pueden encontrarte y escribirte.',
  RECHAZADO:
    'Tu perfil no fue aprobado. Revisa tus datos y comunícate con la DIGER si crees que es un error.',
}

/**
 * CU-17 · Registrar perfil técnico. El técnico/voluntario ve su perfil y su estado de
 * verificación (CU-18), y lo crea o actualiza (el mismo endpoint hace ambas cosas).
 */
export default function MiPerfilTecnico() {
  const [editando, setEditando] = useState(false)
  const {
    data: perfil,
    isPending,
    error,
  } = useQuery({
    queryKey: CLAVE,
    queryFn: obtenerMiPerfil,
  })

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Mi perfil técnico</h1>
      <p className="mt-1 text-slate-600 dark:text-slate-300">
        Así te encuentran los ciudadanos en OficiosYa Pereira.
      </p>

      <div className="mt-5">
        {isPending ? (
          <Cargando texto="Cargando tu perfil…" />
        ) : error ? (
          <Alerta tipo="error">{mensajeDeError(error)}</Alerta>
        ) : !perfil || editando ? (
          <FormularioPerfil perfil={perfil} onTerminar={() => setEditando(false)} />
        ) : (
          <ResumenPerfil perfil={perfil} onEditar={() => setEditando(true)} />
        )}
      </div>
    </>
  )
}

function ResumenPerfil({ perfil, onEditar }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{perfil.full_name}</h2>
        <EstadoVerificacion estado={perfil.verification_status} />
      </div>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        {AVISO_ESTADO[perfil.verification_status]}
      </p>

      <div className="mt-4 flex flex-wrap gap-1">
        {perfil.specialties.map((e) => (
          <Etiqueta key={e} color="azul">
            {nombreEspecialidad(e)}
          </Etiqueta>
        ))}
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <Dato titulo="Experiencia">
          {perfil.experience_years === 1 ? '1 año' : `${perfil.experience_years} años`}
        </Dato>
        <Dato titulo="Valoración">
          <Valoracion tecnico={perfil} />
        </Dato>
        <Dato titulo="WhatsApp de contacto">
          <span className="inline-flex items-center gap-1">
            <Phone className="size-4" aria-hidden="true" />
            {perfil.phone_number}
          </span>
        </Dato>
        <Dato titulo="Zona de trabajo">
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-4" aria-hidden="true" />
            Cerca de {perfil.zona}
          </span>
        </Dato>
      </dl>
      {perfil.bio && <p className="mt-4 text-slate-700 dark:text-slate-200">{perfil.bio}</p>}

      <Boton type="button" variante="secundario" className="mt-5" onClick={onEditar}>
        Editar perfil
      </Boton>
    </section>
  )
}

function Dato({ titulo, children }) {
  return (
    <div>
      <dt className="text-slate-500 dark:text-slate-400">{titulo}</dt>
      <dd className="mt-0.5 font-medium text-slate-900 dark:text-white">{children}</dd>
    </div>
  )
}

function validar(datos) {
  const errores = {}
  if (datos.nombre.trim().length < 3) errores.nombre = 'Escribe tu nombre completo.'
  if (datos.telefono.replace(/[^\d+]/g, '').length < 7)
    errores.telefono = 'Escribe un número de WhatsApp válido.'
  if (datos.especialidades.length === 0) errores.especialidades = 'Elige al menos un oficio.'
  if (datos.experiencia === '' || !Number.isInteger(Number(datos.experiencia)))
    errores.experiencia = 'Escribe los años en números enteros.'
  else if (Number(datos.experiencia) < 0) errores.experiencia = 'No puede ser negativo.'
  if (!datos.coordenadas) errores.coordenadas = 'Marca en el mapa dónde trabajas.'
  return errores
}

function FormularioPerfil({ perfil, onTerminar }) {
  const { usuario } = useAuth()
  const queryClient = useQueryClient()
  const [datos, setDatos] = useState({
    nombre: perfil?.full_name ?? usuario?.full_name ?? '',
    telefono: perfil?.phone_number ?? '',
    especialidades: perfil?.specialties ?? [],
    experiencia: perfil ? String(perfil.experience_years) : '',
    bio: perfil?.bio ?? '',
    coordenadas: perfil?.coordenadas ?? null,
  })
  const [errores, setErrores] = useState({})

  const guardar = useMutation({
    mutationFn: () => guardarMiPerfil(datos),
    onSuccess: (guardado) => {
      queryClient.setQueryData(CLAVE, guardado)
      onTerminar()
    },
  })

  const cambiar = (campo, valor) => setDatos((d) => ({ ...d, [campo]: valor }))
  const alternarEspecialidad = (codigo) =>
    cambiar(
      'especialidades',
      datos.especialidades.includes(codigo)
        ? datos.especialidades.filter((e) => e !== codigo)
        : [...datos.especialidades, codigo],
    )

  return (
    <form
      noValidate
      onSubmit={(e) => {
        e.preventDefault()
        const encontrados = validar(datos)
        setErrores(encontrados)
        if (Object.keys(encontrados).length === 0) guardar.mutate()
      }}
      className="space-y-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900"
    >
      {!perfil && (
        <Alerta tipo="info">
          Aún no tienes perfil. Al registrarlo quedará pendiente hasta que un administrador lo
          verifique.
        </Alerta>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Campo
          etiqueta="Nombre completo"
          autoComplete="name"
          value={datos.nombre}
          error={errores.nombre}
          onChange={(e) => cambiar('nombre', e.target.value)}
        />
        <Campo
          etiqueta="WhatsApp de contacto"
          type="tel"
          autoComplete="tel"
          placeholder="Ej.: +57 310 123 4567"
          value={datos.telefono}
          error={errores.telefono}
          onChange={(e) => cambiar('telefono', e.target.value)}
        />
        <Campo
          etiqueta="Años de experiencia"
          type="number"
          min="0"
          inputMode="numeric"
          value={datos.experiencia}
          error={errores.experiencia}
          onChange={(e) => cambiar('experiencia', e.target.value)}
        />
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-200">
          Oficios
        </legend>
        <div className="flex flex-wrap gap-2">
          {Object.entries(ESPECIALIDADES).map(([codigo, nombre]) => (
            <label
              key={codigo}
              className="flex items-center gap-2 rounded-full border border-slate-300 px-3 py-1.5 text-sm text-slate-700 has-checked:border-marca-600 has-checked:bg-marca-50 dark:border-white/20 dark:text-slate-200 dark:has-checked:border-amber-400 dark:has-checked:bg-amber-400/10"
            >
              <input
                type="checkbox"
                className="size-4 accent-marca-600 dark:accent-amber-500"
                checked={datos.especialidades.includes(codigo)}
                onChange={() => alternarEspecialidad(codigo)}
              />
              {nombre}
            </label>
          ))}
        </div>
        {errores.especialidades && (
          <p className="mt-1 text-sm text-alerta-700 dark:text-red-300">{errores.especialidades}</p>
        )}
      </fieldset>

      <Campo
        como="textarea"
        etiqueta="Cuéntale a la comunidad qué haces (opcional)"
        rows={3}
        maxLength={1000}
        value={datos.bio}
        onChange={(e) => cambiar('bio', e.target.value)}
      />

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-200">
          ¿Dónde trabajas?
        </legend>
        <p className="mb-2 text-sm text-slate-600 dark:text-slate-300">
          Los ciudadanos te encuentran por cercanía. Solo se muestra el barrio aproximado.
        </p>
        <SelectorUbicacion
          valor={datos.coordenadas}
          onCambiar={(c) => cambiar('coordenadas', c)}
          error={errores.coordenadas}
        />
      </fieldset>

      {guardar.error && <Alerta tipo="error">{mensajeDeError(guardar.error)}</Alerta>}

      <div className="flex flex-wrap gap-2">
        <Boton type="submit" cargando={guardar.isPending}>
          {perfil ? 'Guardar cambios' : 'Registrar mi perfil'}
        </Boton>
        {perfil && (
          <Boton type="button" variante="secundario" onClick={onTerminar}>
            Cancelar
          </Boton>
        )}
      </div>
    </form>
  )
}
