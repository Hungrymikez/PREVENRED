import { ClipboardList, HeartPulse, House, Recycle, Siren, Wrench } from 'lucide-react'

/** Secciones del Modo Cotidiano. Las usan el menú y las tarjetas del panel. */
export const MODULOS = [
  { ruta: '/panel', nombre: 'Inicio', Icono: House, exacta: true },
  {
    ruta: '/segundavida',
    nombre: 'SegundaVida',
    descripcion: 'Compra, intercambia o alquila materiales y herramientas de tus vecinos.',
    Icono: Recycle,
  },
  {
    ruta: '/oficiosya',
    nombre: 'OficiosYa',
    descripcion: 'Encuentra técnicos verificados cerca de ti.',
    Icono: Wrench,
  },
  {
    ruta: '/mente-resiliente',
    nombre: 'Mente Resiliente',
    descripcion: 'Cuéntanos cómo estás y encuentra apoyo.',
    Icono: HeartPulse,
  },
]

/** En Modo Emergencia el menú cambia: primero reportar y seguir los casos (CU-04, RF-02). */
export const MODULOS_EMERGENCIA = [
  { ruta: '/panel', nombre: 'Inicio', Icono: House, exacta: true },
  { ruta: '/emergencia', nombre: 'Reportar', Icono: Siren, exacta: true },
  { ruta: '/emergencia/casos', nombre: 'Mis casos', Icono: ClipboardList },
  { ruta: '/mente-resiliente', nombre: 'Apoyo', Icono: HeartPulse },
]
