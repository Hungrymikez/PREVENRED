import { mensajeDeError, textoDeError } from '@/api/client'

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

describe('textoDeError: nunca muestra el texto técnico de axios', () => {
  const deAxios = (status, data = {}) =>
    Object.assign(new Error(`Request failed with status code ${status}`), {
      isAxiosError: true,
      response: { status, data },
    })

  it.each([
    [401, 'Tu sesión terminó. Vuelve a iniciar sesión.'],
    [403, 'Tu tipo de cuenta no tiene permiso para ver o hacer esto.'],
    [404, 'No encontramos lo que buscas.'],
    [500, 'El servidor tuvo un problema. Intenta de nuevo en unos minutos.'],
  ])('un %i sin mensaje del servidor muestra un texto claro', (status, texto) => {
    expect(textoDeError(deAxios(status))).toBe(texto)
  })

  it('prefiere el mensaje del backend cuando lo hay', () => {
    const error = deAxios(403, { error: { message: 'Solo administradores pueden hacer esto.' } })
    expect(textoDeError(error)).toBe('Solo administradores pueden hacer esto.')
  })

  it('respeta los mensajes propios de la app', () => {
    expect(textoDeError(new Error('La publicación no existe.'))).toBe('La publicación no existe.')
  })
})
