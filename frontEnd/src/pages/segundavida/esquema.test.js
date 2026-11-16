import { esquemaPublicacion } from './esquema'

const venta = {
  offerType: 'VENTA',
  title: 'Tejas de zinc',
  description: 'Seis tejas en buen estado.',
  category: 'CONSTRUCCION',
  condition: 'USADO',
  quantity: '6',
  unit: 'unidades',
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

  it('no exige precio en donación', () => {
    expect(
      esquemaPublicacion.safeParse({ ...venta, offerType: 'DONACION', price: '' }).success,
    ).toBe(true)
  })

  it('solo acepta las categorías, estados y modalidades del backend', () => {
    expect(errores({ ...venta, category: 'Pintura' }).category).toBeDefined()
    expect(errores({ ...venta, condition: 'buen_estado' }).condition).toBeDefined()
    expect(errores({ ...venta, offerType: 'INTERCAMBIO' }).offerType).toBeDefined()
  })

  it('exige cantidad mayor a 0 y unidad', () => {
    expect(errores({ ...venta, quantity: '0' }).quantity).toBeDefined()
    expect(errores({ ...venta, unit: ' ' }).unit).toBeDefined()
  })

  it('exige elegir un barrio de la lista', () => {
    expect(errores({ ...venta, zona: 'Mi casa' }).zona).toBeDefined()
  })
})
