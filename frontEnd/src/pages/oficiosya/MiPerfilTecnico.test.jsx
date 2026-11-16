import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { guardarMiPerfil, obtenerMiPerfil } from '@/api/oficiosya'
import { renderConApp } from '@/test/utils'
import MiPerfilTecnico from './MiPerfilTecnico'

vi.mock('@/api/oficiosya', async (original) => ({
  ...(await original()),
  obtenerMiPerfil: vi.fn(),
  guardarMiPerfil: vi.fn(),
}))

// El mapa real (Leaflet) no funciona en el navegador simulado: se reemplaza por un botón.
vi.mock('@/components/mapa/SelectorUbicacion', () => ({
  SelectorUbicacion: ({ onCambiar, error }) => (
    <>
      <button type="button" onClick={() => onCambiar([4.82, -75.67])}>
        Marcar en el mapa
      </button>
      {error && <p>{error}</p>}
    </>
  ),
}))

const TECNICO = { id: 'u9', full_name: 'Julián Ospina', role: 'tecnico_voluntario' }

const PERFIL = {
  id: 't1',
  full_name: 'Julián Ospina',
  phone_number: '+573101234567',
  specialties: ['CARPINTERIA'],
  experience_years: 8,
  bio: 'Muebles y puertas',
  verification_status: 'PENDIENTE',
  rating_average: 0,
  reviews_count: 0,
  coordenadas: [4.82, -75.67],
  zona: 'Villasantana',
}

describe('MiPerfilTecnico (CU-17)', () => {
  beforeEach(() => {
    obtenerMiPerfil.mockReset()
    guardarMiPerfil.mockReset()
  })

  it('muestra el perfil propio con su estado de verificación', async () => {
    obtenerMiPerfil.mockResolvedValue(PERFIL)
    renderConApp(<MiPerfilTecnico />, { auth: { usuario: TECNICO } })

    expect(await screen.findByText('Pendiente de verificación')).toBeInTheDocument()
    expect(screen.getByText('Carpintería')).toBeInTheDocument()
    expect(screen.getByText('8 años')).toBeInTheDocument()
    expect(screen.getByText('Cerca de Villasantana')).toBeInTheDocument()
  })

  it('sin perfil, valida y registra uno nuevo', async () => {
    const usuario = userEvent.setup()
    obtenerMiPerfil.mockResolvedValue(null)
    guardarMiPerfil.mockResolvedValue(PERFIL)
    renderConApp(<MiPerfilTecnico />, { auth: { usuario: TECNICO } })

    const registrar = await screen.findByRole('button', { name: 'Registrar mi perfil' })
    expect(screen.getByLabelText('Nombre completo')).toHaveValue('Julián Ospina')
    await usuario.click(registrar)
    expect(screen.getByText('Elige al menos un oficio.')).toBeInTheDocument()
    expect(screen.getByText('Marca en el mapa dónde trabajas.')).toBeInTheDocument()
    expect(guardarMiPerfil).not.toHaveBeenCalled()

    await usuario.type(screen.getByLabelText('WhatsApp de contacto'), '310 123 4567')
    await usuario.type(screen.getByLabelText('Años de experiencia'), '8')
    await usuario.click(screen.getByLabelText('Carpintería'))
    await usuario.click(screen.getByRole('button', { name: 'Marcar en el mapa' }))
    await usuario.click(registrar)

    expect(guardarMiPerfil).toHaveBeenCalledWith({
      nombre: 'Julián Ospina',
      telefono: '310 123 4567',
      especialidades: ['CARPINTERIA'],
      experiencia: '8',
      bio: '',
      coordenadas: [4.82, -75.67],
    })
    expect(await screen.findByText('Pendiente de verificación')).toBeInTheDocument()
  })

  it('edita el perfil existente', async () => {
    const usuario = userEvent.setup()
    obtenerMiPerfil.mockResolvedValue(PERFIL)
    guardarMiPerfil.mockResolvedValue({ ...PERFIL, specialties: ['CARPINTERIA', 'PINTURA'] })
    renderConApp(<MiPerfilTecnico />, { auth: { usuario: TECNICO } })

    await usuario.click(await screen.findByRole('button', { name: 'Editar perfil' }))
    await usuario.click(screen.getByLabelText('Pintura'))
    await usuario.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(guardarMiPerfil.mock.calls[0][0].especialidades).toEqual(['CARPINTERIA', 'PINTURA'])
    expect(await screen.findByText('Pintura')).toBeInTheDocument()
  })
})
