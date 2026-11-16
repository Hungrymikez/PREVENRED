/** Roles que maneja el backend (backend/src/prevenred/auth/domain/role.py). */
export const ROLES = {
  CIUDADANO: 'ciudadano',
  TECNICO_VOLUNTARIO: 'tecnico_voluntario',
  INSPECTOR: 'inspector',
  ADMINISTRADOR: 'administrador',
  PROFESIONAL_SALUD: 'profesional_salud',
}

export const NOMBRE_ROL = {
  [ROLES.CIUDADANO]: 'Ciudadano',
  [ROLES.TECNICO_VOLUNTARIO]: 'Técnico / voluntario',
  [ROLES.INSPECTOR]: 'Inspector',
  [ROLES.ADMINISTRADOR]: 'Administrador',
  [ROLES.PROFESIONAL_SALUD]: 'Profesional de salud',
}

/**
 * Personal de atención: ven y gestionan todos los casos reportados (CU-39, CU-40).
 * El Administrador además controla el modo operacional (CU-04, RN-01).
 */
export const ROLES_PERSONAL = [ROLES.INSPECTOR, ROLES.ADMINISTRADOR]

/** Quienes reportan emergencias y siguen sus propios casos (CU-29 a CU-32). */
export const ROLES_REPORTANTES = [
  ROLES.CIUDADANO,
  ROLES.TECNICO_VOLUNTARIO,
  ROLES.PROFESIONAL_SALUD,
]

export const esPersonal = (rol) => ROLES_PERSONAL.includes(rol)
export const esAdministrador = (rol) => rol === ROLES.ADMINISTRADOR
