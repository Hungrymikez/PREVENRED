import { esquemaRegistro } from './esquemas'

const valido = {
  full_name: 'Sara Salas',
  email: 'sara@correo.com',
  password: 'clave-segura',
  confirmar: 'clave-segura',
  role: 'ciudadano',
  neighborhood: 'Cuba',
  phone: '',
  skills: '',
  accepted_terms: true,
}

function erroresDe(datos) {
  const resultado = esquemaRegistro.safeParse(datos)
  return resultado.success ? {} : resultado.error.flatten().fieldErrors
}

describe('esquemaRegistro', () => {
  it('acepta un registro completo', () => {
    expect(esquemaRegistro.safeParse(valido).success).toBe(true)
  })

  it('exige contraseña de al menos 8 caracteres', () => {
    expect(erroresDe({ ...valido, password: 'corta', confirmar: 'corta' }).password).toBeDefined()
  })

  it('exige que las contraseñas coincidan', () => {
    expect(erroresDe({ ...valido, confirmar: 'otra-clave' }).confirmar).toEqual([
      'Las contraseñas no coinciden.',
    ])
  })

  it('exige aceptar el aviso de privacidad', () => {
    expect(erroresDe({ ...valido, accepted_terms: false }).accepted_terms).toBeDefined()
  })

  it('no permite roles que no se auto-registran', () => {
    expect(erroresDe({ ...valido, role: 'administrador' }).role).toBeDefined()
  })
})
