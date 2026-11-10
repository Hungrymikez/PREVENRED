import { agregarFotos, MAXIMO_FOTOS, TAMANO_MAXIMO_FOTO_MB } from './fotos'

const foto = (nombre, tipo = 'image/jpeg', bytes = 10) =>
  new File([new Uint8Array(bytes)], nombre, { type: tipo })

describe('agregarFotos (CU-11 con CU-47)', () => {
  it('acepta JPG, PNG y WEBP', () => {
    const nuevas = [foto('a.jpg'), foto('b.png', 'image/png'), foto('c.webp', 'image/webp')]
    expect(agregarFotos([], nuevas)).toEqual({ fotos: nuevas, error: '' })
  })

  it('rechaza lo que no es una foto permitida (E1) y conserva las válidas', () => {
    const buena = foto('a.jpg')
    const { fotos, error } = agregarFotos(
      [],
      [foto('virus.exe', 'application/x-msdownload'), buena],
    )
    expect(fotos).toEqual([buena])
    expect(error).toMatch('JPG, PNG o WEBP')
  })

  it(`rechaza fotos de más de ${TAMANO_MAXIMO_FOTO_MB} MB (E2)`, () => {
    const pesada = foto('grande.jpg', 'image/jpeg', TAMANO_MAXIMO_FOTO_MB * 1024 * 1024 + 1)
    const { fotos, error } = agregarFotos([], [pesada])
    expect(fotos).toEqual([])
    expect(error).toMatch(`${TAMANO_MAXIMO_FOTO_MB} MB`)
  })

  it(`no deja pasar de ${MAXIMO_FOTOS} fotos (A1)`, () => {
    const actuales = Array.from({ length: MAXIMO_FOTOS - 1 }, (_, i) => foto(`${i}.jpg`))
    const { fotos, error } = agregarFotos(actuales, [foto('x.jpg'), foto('y.jpg')])
    expect(fotos).toHaveLength(MAXIMO_FOTOS)
    expect(error).toMatch(`hasta ${MAXIMO_FOTOS}`)
  })
})
