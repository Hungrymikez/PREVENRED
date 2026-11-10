import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { publicar } from '@/api/segundavida'
import { SelectorFotos } from './SelectorFotos'

const foto = (nombre, tipo = 'image/jpeg') => new File(['bytes'], nombre, { type: tipo })

function ConEstado() {
  const [fotos, setFotos] = useState([])
  return <SelectorFotos fotos={fotos} onCambiar={setFotos} />
}

describe('SelectorFotos (CU-11 con CU-47)', () => {
  beforeEach(() => {
    let n = 0
    // jsdom no implementa las URLs de archivos locales.
    vi.stubGlobal(
      'URL',
      Object.assign(URL, {
        createObjectURL: vi.fn(() => `blob:prueba-${(n += 1)}`),
        revokeObjectURL: vi.fn(),
      }),
    )
  })
  afterEach(() => vi.unstubAllGlobals())

  it('muestra la vista previa de cada foto y permite quitarlas (A2)', async () => {
    const usuario = userEvent.setup()
    render(<ConEstado />)

    await usuario.upload(screen.getByLabelText(/agregar fotos/i), [
      foto('a.jpg'),
      foto('b.png', 'image/png'),
    ])
    expect(screen.getAllByRole('img')).toHaveLength(2)

    await usuario.click(screen.getByRole('button', { name: 'Quitar foto 1' }))
    expect(screen.getAllByRole('img')).toHaveLength(1)
    expect(screen.getByAltText('Foto 1 de la publicación')).toBeInTheDocument()
  })

  it('avisa cuando un archivo no es una foto permitida (E1)', async () => {
    const usuario = userEvent.setup({ applyAccept: false })
    render(<ConEstado />)

    await usuario.upload(
      screen.getByLabelText(/agregar fotos/i),
      foto('doc.pdf', 'application/pdf'),
    )
    expect(screen.getByRole('alert')).toHaveTextContent('JPG, PNG o WEBP')
    expect(screen.queryAllByRole('img')).toHaveLength(0)
  })

  it('la publicación guarda una URL por cada foto', async () => {
    vi.useFakeTimers()
    const promesa = publicar(
      {
        offerType: 'VENTA',
        title: 'Tejas',
        description: 'Tejas de zinc en buen estado',
        category: 'Construcción',
        condition: 'buen_estado',
        quantity: 2,
        price: 1000,
        zona: 'Cuba',
      },
      'Sara Salas',
      [foto('a.jpg'), foto('b.jpg')],
    )
    await vi.runAllTimersAsync()
    expect((await promesa).mediaUrls).toEqual(['blob:prueba-1', 'blob:prueba-2'])
    vi.useRealTimers()
  })
})
