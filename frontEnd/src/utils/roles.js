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
