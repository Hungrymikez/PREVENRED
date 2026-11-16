import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router'
import { enlaceWhatsapp, obtenerTecnico } from '@/api/oficiosya'
import { renderConApp, USUARIO_PRUEBA } from '@/test/utils'
import PerfilTecnico from './PerfilTecnico'

vi.mock('@/api/oficiosya', async (original) => ({
  ...(await original()),
  obtenerTecnico: vi.fn(),
  enlaceWhatsapp: vi.fn(),
}))

// El mapa real (Leaflet) no funciona en el navegador simulado.
vi.mock('@/components/mapa/Mapa', () => ({ Mapa: () => null }))

describe('PerfilTecnico (CU-19, CU-22)', () => {
  beforeAll(() => {
    // jsdom no implementa los métodos de <dialog>.
    HTMLDialogElement.prototype.showModal ??= function () {
      this.open = true
    }
    HTMLDialogElement.prototype.close ??= function () {
      this.open = false
    }
  })

  it('muestra el perfil y abre WhatsApp con el enlace del backend tras autorizar', async () => {
    obtenerTecnico.mockResolvedValue({
      id: 't1',
      full_name: 'Natalia Gómez',
      specialties: ['PINTURA'],
      experience_years: 1,
      bio: 'Pinto fachadas',
      verification_status: 'VERIFICADO',
      rating_average: 0,
      reviews_count: 0,
      coordenadas: [4.8133, -75.6961],
      zona: 'Centro',
    })
    enlaceWhatsapp.mockResolvedValue('https://wa.me/573001112233?text=Hola')
    renderConApp(
      <Routes>
        <Route path="/oficiosya/:id" element={<PerfilTecnico />} />
      </Routes>,
      { auth: { usuario: USUARIO_PRUEBA }, ruta: '/oficiosya/t1' },
    )

    expect(await screen.findByRole('heading', { name: /Natalia Gómez/ })).toBeInTheDocument()
    expect(obtenerTecnico).toHaveBeenCalledWith('t1')
    expect(screen.getByText('Sin reseñas todavía')).toBeInTheDocument()
    expect(screen.getByText('1 año de experiencia')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Escribir por WhatsApp/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Sí, autorizo', hidden: true }))
    const enlace = await screen.findByRole('link', { name: /Abrir WhatsApp/, hidden: true })
    expect(enlace).toHaveAttribute('href', 'https://wa.me/573001112233?text=Hola')
  })
})
