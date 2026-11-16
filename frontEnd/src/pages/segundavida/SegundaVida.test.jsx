import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listarPublicaciones, publicar } from '@/api/segundavida'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import Publicar from './Publicar'
import SegundaVida from './SegundaVida'

vi.mock('@/api/segundavida', async (original) => ({
  ...(await original()),
  listarPublicaciones: vi.fn(),
  publicar: vi.fn(),
}))

const PUBLICACION = {
  id: 'm1',
  title: 'Tejas de zinc',
  description: 'Seis tejas',
  category: 'CONSTRUCCION',
  offerType: 'VENTA',
  condition: 'BUENO',
  quantity: 6,
  unit: 'unidades',
  price: 30000,
  coordenadas: [4.796, -75.731],
  zona: 'Cuba',
  distanciaKm: 0.2,
  ownerName: 'Sara S.',
  mediaUrls: ['/static/uploads/a.jpg'],
}

describe('SegundaVida (CU-12)', () => {
  beforeEach(() => listarPublicaciones.mockReset())

  it('busca cerca del barrio de la cuenta y muestra la foto real con nombres en español', async () => {
    listarPublicaciones.mockResolvedValue([PUBLICACION])
    renderConApp(<SegundaVida />, { auth: { usuario: USUARIO_PRUEBA } })

    expect(await screen.findByText('Tejas de zinc')).toBeInTheDocument()
    expect(screen.getByAltText('Foto de Tejas de zinc')).toHaveAttribute(
      'src',
      '/static/uploads/a.jpg',
    )
    const tarjeta = screen.getByRole('link', { name: /tejas de zinc/i })
    expect(tarjeta).toHaveTextContent('Construcción')
    expect(tarjeta).toHaveTextContent('Buen estado')
    expect(listarPublicaciones).toHaveBeenCalledWith(
      expect.objectContaining({ modalidad: 'VENTA', cerca: 'Cuba' }),
    )
  })

  it('la pestaña Donaciones busca con el tipo de oferta del backend', async () => {
    listarPublicaciones.mockResolvedValue([])
    const usuario = userEvent.setup()
    renderConApp(<SegundaVida />, { auth: { usuario: USUARIO_PRUEBA } })

    await usuario.click(screen.getByRole('button', { name: 'Donaciones' }))
    expect(listarPublicaciones).toHaveBeenLastCalledWith(
      expect.objectContaining({ modalidad: 'DONACION' }),
    )
  })
})

describe('Publicar (CU-11)', () => {
  beforeEach(() => {
    publicar.mockReset()
    vi.stubGlobal(
      'URL',
      Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:x'), revokeObjectURL: vi.fn() }),
    )
  })
  afterEach(() => vi.unstubAllGlobals())

  it('envía los datos con los valores del backend junto con las fotos elegidas', async () => {
    publicar.mockResolvedValue(PUBLICACION)
    const usuario = userEvent.setup()
    renderConApp(<Publicar />, { auth: { usuario: USUARIO_PRUEBA } })

    await usuario.type(screen.getByLabelText('Título'), 'Tejas de zinc')
    await usuario.type(screen.getByLabelText('Descripción'), 'Seis tejas en buen estado')
    await usuario.selectOptions(screen.getByLabelText('Categoría'), 'Construcción')
    await usuario.selectOptions(screen.getByLabelText('Estado'), 'Buen estado')
    await usuario.type(screen.getByLabelText('Precio (COP)'), '30000')
    const foto = new File(['bytes'], 'tejas.jpg', { type: 'image/jpeg' })
    await usuario.upload(screen.getByLabelText(/agregar fotos/i), foto)
    await usuario.click(screen.getByRole('button', { name: 'Publicar' }))

    expect(publicar).toHaveBeenCalledWith(
      expect.objectContaining({
        offerType: 'VENTA',
        category: 'CONSTRUCCION',
        condition: 'BUENO',
        unit: 'unidades',
        zona: 'Cuba',
      }),
      [foto],
    )
  })
})
