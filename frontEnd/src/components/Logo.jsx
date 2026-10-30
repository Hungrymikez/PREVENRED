import { ShieldCheck } from 'lucide-react'
import { Link } from 'react-router'

export function Logo({ a = '/' }) {
  return (
    <Link to={a} className="inline-flex items-center gap-2 text-xl font-bold text-marca-900">
      <ShieldCheck className="size-7 text-marca-600" aria-hidden="true" />
      PrevenRed
    </Link>
  )
}
