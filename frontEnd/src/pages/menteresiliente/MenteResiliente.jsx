import { useMutation } from '@tanstack/react-query'
import { HeartHandshake, Phone, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import {
  enviarRegistro,
  LINEAS_DE_APOYO,
  NIVELES_ANIMO,
  otorgarConsentimiento,
  tieneConsentimiento,
} from '@/api/bienestar'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Campo } from '@/components/ui/Campo'
import { useAuth } from '@/hooks/useAuth'

/** Mente Resiliente: consentimiento (CU-24), registro de bienestar (CU-23) y apoyo (CU-27). */
export default function MenteResiliente() {
  const [consentimiento, setConsentimiento] = useState(tieneConsentimiento)

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Mente Resiliente</h1>
        <p className="text-slate-600">Un espacio para contar cómo estás. Sin juicios.</p>
      </div>

      {consentimiento ? (
        <RegistroBienestar />
      ) : (
        <Consentimiento onAceptar={() => setConsentimiento(true)} />
      )}
      <ApoyoProfesional />
    </div>
  )
}

/** CU-24. Sin consentimiento no se recopila ninguna respuesta. */
function Consentimiento({ onAceptar }) {
  const [acepta, setAcepta] = useState(false)
  const aceptar = useMutation({ mutationFn: otorgarConsentimiento, onSuccess: onAceptar })

  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm" aria-labelledby="titulo-consentimiento">
      <h2
        id="titulo-consentimiento"
        className="flex items-center gap-2 font-semibold text-slate-900"
      >
        <ShieldCheck className="size-5 text-marca-600" aria-hidden="true" />
        Antes de empezar
      </h2>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
        <li>Tu respuesta se analiza junto con la de otros vecinos, por barrio, y sin tu nombre.</li>
        <li>No es un diagnóstico ni una evaluación de tu salud.</li>
        <li>Estos datos nunca se usan con fines comerciales.</li>
        <li>Puedes dejar de participar cuando quieras.</li>
      </ul>
      <label className="mt-4 flex items-start gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          className="mt-0.5 size-4 accent-marca-600"
          checked={acepta}
          onChange={(e) => setAcepta(e.target.checked)}
        />
        Entiendo y acepto participar de forma anónima.
      </label>
      <Boton
        className="mt-4"
        disabled={!acepta}
        cargando={aceptar.isPending}
        onClick={() => aceptar.mutate()}
      >
        Continuar
      </Boton>
    </section>
  )
}

/** CU-23. Nivel de ánimo (5 niveles) y texto opcional. */
function RegistroBienestar() {
  const { usuario } = useAuth()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ defaultValues: { animo: '', texto: '' } })

  const envio = useMutation({
    mutationFn: ({ animo, texto }) =>
      enviarRegistro({ animo: Number(animo), texto: texto.trim(), barrio: usuario.neighborhood }),
  })

  if (envio.isSuccess) {
    const animoBajo = envio.variables.animo <= 2
    return (
      <section className="rounded-2xl bg-white p-6 shadow-sm" role="status">
        <h2 className="text-lg font-semibold text-slate-900">Gracias por contarnos cómo estás</h2>
        <p className="mt-1 text-slate-700">
          Tu respuesta ayuda a entender cómo está tu barrio y a llevar apoyo donde más se necesita.
        </p>
        {animoBajo && (
          <p className="mt-3 text-slate-700">
            Si te está costando, no tienes que pasar por esto sin ayuda. Abajo encuentras a quién
            acudir.
          </p>
        )}
        <Boton
          variante="secundario"
          className="mt-4"
          onClick={() => {
            reset()
            envio.reset()
          }}
        >
          Enviar otro registro
        </Boton>
      </section>
    )
  }

  return (
    <form
      onSubmit={handleSubmit((datos) => envio.mutate(datos))}
      noValidate
      className="space-y-5 rounded-2xl bg-white p-6 shadow-sm"
    >
      {envio.error && (
        <Alerta tipo="error">No se pudo enviar. Revisa tu conexión e intenta de nuevo.</Alerta>
      )}

      <fieldset>
        <legend className="font-semibold text-slate-900">¿Cómo te sientes esta semana?</legend>
        <div className="mt-3 grid grid-cols-5 gap-2">
          {NIVELES_ANIMO.map((nivel) => (
            <label
              key={nivel.valor}
              className="flex cursor-pointer flex-col items-center gap-1 rounded-xl border border-slate-300 p-2 text-center has-checked:border-marca-600 has-checked:bg-marca-50 has-focus-visible:ring-2 has-focus-visible:ring-marca-600"
            >
              <input
                type="radio"
                value={nivel.valor}
                className="sr-only"
                {...register('animo', { required: 'Elige cómo te sientes.' })}
              />
              <span className="text-2xl" aria-hidden="true">
                {nivel.emoji}
              </span>
              <span className="text-xs font-medium text-slate-800">{nivel.nombre}</span>
            </label>
          ))}
        </div>
        {errors.animo && <p className="mt-1 text-sm text-alerta-700">{errors.animo.message}</p>}
      </fieldset>

      <Campo
        como="textarea"
        rows={4}
        maxLength={500}
        etiqueta="¿Quieres contarnos algo más? (opcional)"
        placeholder="Escribe lo que quieras compartir…"
        ayuda="Máximo 500 caracteres. No escribas tu nombre ni datos personales."
        {...register('texto')}
      />

      <Boton type="submit" cargando={envio.isPending} className="w-full">
        Enviar
      </Boton>
    </form>
  )
}

/** CU-27. Siempre visible, haya o no consentimiento. */
function ApoyoProfesional() {
  return (
    <section
      className="rounded-2xl border border-marca-100 bg-marca-50 p-6"
      aria-labelledby="titulo-apoyo"
    >
      <h2 id="titulo-apoyo" className="flex items-center gap-2 font-semibold text-marca-900">
        <HeartHandshake className="size-5" aria-hidden="true" />
        ¿Necesitas hablar con alguien ahora?
      </h2>
      <ul className="mt-3 space-y-3">
        {LINEAS_DE_APOYO.map((linea) => (
          <li
            key={linea.nombre}
            className="flex items-center justify-between gap-3 rounded-xl bg-white p-3"
          >
            <div>
              <p className="font-medium text-slate-900">{linea.nombre}</p>
              <p className="text-sm text-slate-600">{linea.detalle}</p>
            </div>
            {linea.telefono && (
              <a
                href={`tel:${linea.telefono}`}
                className="inline-flex shrink-0 items-center gap-1 rounded-lg bg-marca-600 px-3 py-2 font-medium text-white hover:bg-marca-700"
              >
                <Phone className="size-4" aria-hidden="true" />
                {linea.telefono}
              </a>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
