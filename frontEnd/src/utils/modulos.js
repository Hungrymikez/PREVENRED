import { HeartPulse, House, Recycle, Wrench } from 'lucide-react'

/** Secciones del Modo Cotidiano. Las usan el menú y las tarjetas del panel. */
export const MODULOS = [
  { ruta: '/panel', nombre: 'Inicio', Icono: House },
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
