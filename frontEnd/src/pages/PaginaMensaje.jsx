import { Link } from 'react-router'

/** Página simple de aviso: 404, sin permiso, etc. */
function PaginaMensaje({ codigo, titulo, texto }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-marca-600">{codigo}</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900">{titulo}</h1>
      <p className="mt-2 text-slate-600">{texto}</p>
      <Link
        to="/"
        className="mt-6 rounded-lg bg-marca-600 px-4 py-2.5 font-medium text-white hover:bg-marca-700"
      >
        Volver al inicio
      </Link>
    </main>
  )
}

export function NoEncontrado() {
  return (
    <PaginaMensaje
      codigo="404"
      titulo="Página no encontrada"
      texto="La dirección que buscas no existe o cambió."
    />
  )
}

export function SinPermiso() {
  return (
    <PaginaMensaje
      codigo="403"
      titulo="No tienes acceso"
      texto="Tu tipo de cuenta no puede ver esta sección."
    />
  )
}
