import { Link } from 'react-router'
import { useAuth } from '@/hooks/useAuth'
import { useModo } from '@/hooks/useModo'
import { AccionesEmergencia } from '@/pages/emergencia/AccionesEmergencia'
import { MODULOS } from '@/utils/modulos'

/**
 * Página de inicio con sesión. En Modo Emergencia lo primero son los reportes;
 * los módulos del día a día quedan debajo.
 */
export default function Panel() {
  const { usuario } = useAuth()
  const { enEmergencia } = useModo()
  const nombre = usuario.full_name.split(' ')[0]

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900">Hola, {nombre}</h1>

      {enEmergencia ? (
        <section className="mt-4" aria-labelledby="titulo-emergencia">
          <h2 id="titulo-emergencia" className="mb-3 font-semibold text-alerta-700">
            ¿Necesitas reportar algo?
          </h2>
          <AccionesEmergencia />
        </section>
      ) : (
        <p className="mt-1 text-slate-600">¿Qué quieres hacer hoy en {usuario.neighborhood}?</p>
      )}

      <ul className="mt-6 grid gap-4 sm:grid-cols-3">
        {MODULOS.filter((m) => m.descripcion).map(({ ruta, nombre, descripcion, Icono }) => (
          <li key={ruta}>
            <Link
              to={ruta}
              className="block h-full rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-marca-600 hover:shadow-sm"
            >
              <Icono className="size-8 text-marca-600" aria-hidden="true" />
              <h2 className="mt-3 font-semibold text-slate-900">{nombre}</h2>
              <p className="mt-1 text-sm text-slate-600">{descripcion}</p>
            </Link>
          </li>
        ))}
      </ul>
    </>
  )
}
