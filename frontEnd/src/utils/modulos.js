import {
  ChartColumn,
  ClipboardCheck,
  ClipboardList,
  HandHeart,
  HandHelping,
  HeartPulse,
  House,
  Inbox,
  Package,
  Recycle,
  ScrollText,
  Siren,
  UserCheck,
  UserCog,
  Users,
  Wrench,
} from 'lucide-react'
import { ROLES, ROLES_PERSONAL, ROLES_REPORTANTES } from '@/utils/roles'

const SOLO_ADMIN = [ROLES.ADMINISTRADOR]
const SOLO_TECNICO = [ROLES.TECNICO_VOLUNTARIO]

/** Bandeja de todos los casos: solo Inspector y Administrador (CU-39). */
const CASOS = {
  ruta: '/casos',
  nombre: 'Casos',
  descripcion: 'Revisa los reportes de la comunidad, asígnalos y actualiza su estado.',
  Icono: Inbox,
  tono: 'gris',
  roles: ROLES_PERSONAL,
  grupo: 'gestion',
}

/**
 * Secciones de la app. Las usan el menú (barra superior y barra inferior en celular) y las
 * tarjetas del panel.
 *  - `roles` limita quién la ve; sin `roles`, la ven todos (el backend vuelve a validar).
 *  - `soloPanel`: no va en el menú, solo como tarjeta del panel (para no saturar el menú).
 *  - `grupo: 'gestion'`: en el panel va en la sección de gestión, no en "Servicios".
 *  - `tono` es el color propio de cada tarjeta del panel (ver TONOS en Panel.jsx).
 */
export const MODULOS = [
  { ruta: '/panel', nombre: 'Inicio', Icono: House, exacta: true },
  {
    ruta: '/segundavida',
    nombre: 'SegundaVida',
    tono: 'verde',
    descripcion: 'Compra, dona o alquila materiales y herramientas de tus vecinos.',
    Icono: Recycle,
  },
  {
    ruta: '/oficiosya',
    nombre: 'OficiosYa',
    tono: 'naranja',
    descripcion: 'Encuentra técnicos verificados cerca de ti.',
    Icono: Wrench,
  },
  {
    ruta: '/mente-resiliente',
    nombre: 'Mente Resiliente',
    tono: 'rosa',
    descripcion: 'Cuéntanos cómo estás y encuentra apoyo.',
    Icono: HeartPulse,
  },
  CASOS,

  // Quien reporta (ciudadano, técnico, profesional de salud)
  {
    ruta: '/emergencia/casos',
    nombre: 'Mis casos',
    descripcion: 'Sigue el estado de los reportes que has hecho.',
    Icono: ClipboardList,
    tono: 'gris',
    roles: ROLES_REPORTANTES,
    soloPanel: true,
  },
  {
    ruta: '/donar',
    nombre: 'Donar',
    descripcion: 'Ofrece agua, alimentos o herramientas para quien lo necesite.',
    Icono: HandHeart,
    tono: 'azul',
    roles: ROLES_REPORTANTES,
    soloPanel: true,
  },

  // Técnico / voluntario (CU-17, CU-44, CU-38)
  {
    ruta: '/oficiosya/mi-perfil',
    nombre: 'Mi perfil técnico',
    descripcion: 'Crea o actualiza tu perfil para aparecer en OficiosYa.',
    Icono: UserCog,
    tono: 'naranja',
    roles: SOLO_TECNICO,
    soloPanel: true,
    grupo: 'gestion',
  },
  {
    ruta: '/voluntariado',
    nombre: 'Voluntariado',
    descripcion: 'Inscríbete como voluntario y revisa tus tareas asignadas.',
    Icono: HandHelping,
    tono: 'azul',
    roles: SOLO_TECNICO,
    soloPanel: true,
    grupo: 'gestion',
  },

  // Inspector y Administrador (CU-34 a CU-36, CU-43)
  {
    ruta: '/inspecciones',
    nombre: 'Censo e inspecciones',
    descripcion: 'Registra y consulta las inspecciones de inmuebles.',
    Icono: ClipboardCheck,
    tono: 'gris',
    roles: ROLES_PERSONAL,
    soloPanel: true,
    grupo: 'gestion',
  },
  {
    ruta: '/voluntariado/asignar',
    nombre: 'Asignar voluntarios',
    descripcion: 'Asigna voluntarios disponibles a los casos que lo necesitan.',
    Icono: Users,
    tono: 'azul',
    roles: ROLES_PERSONAL,
    soloPanel: true,
    grupo: 'gestion',
  },

  // Solo Administrador (CU-45, CU-18, CU-41/42, CU-09)
  {
    ruta: '/admin/tablero',
    nombre: 'Tablero municipal',
    descripcion: 'Indicadores de la ciudad, bienestar por barrio y exportación de reportes.',
    Icono: ChartColumn,
    tono: 'azul',
    roles: SOLO_ADMIN,
    soloPanel: true,
    grupo: 'gestion',
  },
  {
    ruta: '/admin/tecnicos',
    nombre: 'Verificar técnicos',
    descripcion: 'Aprueba o rechaza los perfiles de técnicos pendientes.',
    Icono: UserCheck,
    tono: 'naranja',
    roles: SOLO_ADMIN,
    soloPanel: true,
    grupo: 'gestion',
  },
  {
    ruta: '/donaciones',
    nombre: 'Gestión de donaciones',
    descripcion: 'Revisa necesidades y ofertas y ejecuta el emparejamiento.',
    Icono: Package,
    tono: 'verde',
    roles: SOLO_ADMIN,
    soloPanel: true,
    grupo: 'gestion',
  },
  {
    ruta: '/admin/auditoria',
    nombre: 'Auditoría',
    descripcion: 'Consulta el registro de acciones sobre la plataforma.',
    Icono: ScrollText,
    tono: 'gris',
    roles: SOLO_ADMIN,
    soloPanel: true,
    grupo: 'gestion',
  },
]

/**
 * En Modo Emergencia el menú cambia (CU-04, RF-02): quien reporta ve primero Reportar y
 * Mis casos; el personal de atención ve la bandeja de Casos.
 */
export const MODULOS_EMERGENCIA = [
  { ruta: '/panel', nombre: 'Inicio', Icono: House, exacta: true },
  { ruta: '/emergencia', nombre: 'Reportar', Icono: Siren, exacta: true, roles: ROLES_REPORTANTES },
  {
    ruta: '/emergencia/casos',
    nombre: 'Mis casos',
    Icono: ClipboardList,
    roles: ROLES_REPORTANTES,
  },
  CASOS,
  { ruta: '/mente-resiliente', nombre: 'Apoyo', Icono: HeartPulse },
]

/** Las secciones que puede ver un rol. */
export function modulosParaRol(lista, rol) {
  return lista.filter((m) => !m.roles || m.roles.includes(rol))
}
