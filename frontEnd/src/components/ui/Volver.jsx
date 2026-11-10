import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'

export function Volver({ a, children = 'Volver' }) {
  return (
    <Link
      to={a}
      className="inline-flex items-center gap-1 text-sm font-medium text-marca-700 hover:underline dark:text-amber-400"
    >
      <ArrowLeft className="size-4" aria-hidden="true" />
      {children}
    </Link>
  )
}
