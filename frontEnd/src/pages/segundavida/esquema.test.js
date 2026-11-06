import { esquemaPublicacion } from './esquema'

const venta = {
  offerType: 'VENTA',
  title: 'Tejas de zinc',
  description: 'Seis tejas en buen estado.',
  category: 'Construcción',
  condition: 'usado',
  quantity: '6',
  price: '30000',
  zona: 'Cuba',
}

function errores(datos) {
  const r = esquemaPublicacion.safeParse(datos)
  return r.success ? {} : r.error.flatten().fieldErrors
}

describe('esquemaPublicacion (CU-11)', () => {
  it('acepta una venta completa', () => {
    expect(esquemaPublicacion.safeParse(venta).success).toBe(true)
  })

  it('exige precio en venta y en alquiler', () => {
    expect(errores({ ...venta, price: '' }).price).toEqual(['Indica el precio.'])
    expect(errores({ ...venta, offerType: 'ALQUILER', price: '0' }).price).toBeDefined()
  })

  it('no exige precio en intercambio', () => {
    expect(
      esquemaPublicacion.safeParse({ ...venta, offerType: 'INTERCAMBIO', price: '' }).success,
    ).toBe(true)
  })

  it('exige elegir un barrio de la lista', () => {
    expect(errores({ ...venta, zona: 'Mi casa' }).zona).toBeDefined()
  })
})
