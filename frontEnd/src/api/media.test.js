import { api } from '@/api/client'
import { subirArchivo, urlPublica } from './media'

vi.mock('@/api/client', async (original) => ({
  ...(await original()),
  api: { post: vi.fn() },
}))

describe('subirArchivo (CU-47)', () => {
  beforeEach(() => api.post.mockReset())

  it('envía el archivo en el campo "file" y devuelve la URL pública', async () => {
    api.post.mockResolvedValue({ data: { url: '/static/uploads/abc.jpg' } })
    const foto = new File(['bytes'], 'tejas.jpg', { type: 'image/jpeg' })

    await expect(subirArchivo(foto)).resolves.toBe('/static/uploads/abc.jpg')
    const [url, formulario] = api.post.mock.calls[0]
    expect(url).toBe('/media/upload')
    expect(formulario.get('file').name).toBe('tejas.jpg')
  })

  it('a un Blob sin nombre (reporte guardado sin conexión) le pone uno según su tipo', async () => {
    api.post.mockResolvedValue({ data: { url: '/static/uploads/x.png' } })
    await subirArchivo(new Blob(['bytes'], { type: 'image/png' }))
    expect(api.post.mock.calls[0][1].get('file').name).toBe('foto.png')
  })
})

describe('urlPublica', () => {
  afterEach(() => vi.unstubAllEnvs())

  it('deja igual la ruta relativa cuando la API está en el mismo sitio', () => {
    vi.stubEnv('VITE_API_URL', undefined)
    expect(urlPublica('/static/uploads/a.jpg')).toBe('/static/uploads/a.jpg')
  })

  it('usa el dominio de la API cuando está en otro sitio', () => {
    vi.stubEnv('VITE_API_URL', 'https://api.prevenred.co/api/v1')
    expect(urlPublica('/static/uploads/a.jpg')).toBe(
      'https://api.prevenred.co/static/uploads/a.jpg',
    )
  })
})
