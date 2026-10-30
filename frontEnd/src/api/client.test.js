import { mensajeDeError } from '@/api/client'

describe('mensajeDeError', () => {
  it('usa el mensaje de los errores de negocio del backend', () => {
    const error = {
      response: {
        data: { error: { code: 'conflict', message: 'Ese correo ya está registrado.' } },
      },
    }
    expect(mensajeDeError(error)).toBe('Ese correo ya está registrado.')
  })

  it('une los mensajes de validación de FastAPI (422)', () => {
    const error = {
      response: { data: { detail: [{ msg: 'Campo requerido' }, { msg: 'Muy corto' }] } },
    }
    expect(mensajeDeError(error)).toBe('Campo requerido. Muy corto')
  })

  it('avisa cuando no hay conexión con el servidor', () => {
    expect(mensajeDeError({ request: {} })).toMatch(/no hay conexión/i)
  })
})
