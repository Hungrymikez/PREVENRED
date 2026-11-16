import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router'
import { PantallaCarga } from '@/components/ui/PantallaCarga'
import { LayoutAuth } from '@/layouts/LayoutAuth'
import { LayoutPrincipal } from '@/layouts/LayoutPrincipal'
import Inicio from '@/pages/Inicio'
import { NoEncontrado, SinPermiso } from '@/pages/PaginaMensaje'
import {
  cargarDetalleCaso,
  cargarEmergencia,
  cargarMisCasos,
  cargarPanel,
  cargarReportar,
} from '@/routes/paginas'
import { RutaEmergencia } from '@/routes/RutaEmergencia'
import { RutaProtegida, RutaPublica } from '@/routes/RutaProtegida'
import { ROLES, ROLES_PERSONAL, ROLES_REPORTANTES } from '@/utils/roles'

// Cada página se descarga solo cuando se visita (la app abre más rápido, sobre todo en celular).
const Login = lazy(() => import('@/pages/auth/Login'))
const Registro = lazy(() => import('@/pages/auth/Registro'))
const Panel = lazy(cargarPanel)
const SegundaVida = lazy(() => import('@/pages/segundavida/SegundaVida'))
const DetallePublicacion = lazy(() => import('@/pages/segundavida/DetallePublicacion'))
const Publicar = lazy(() => import('@/pages/segundavida/Publicar'))
const OficiosYa = lazy(() => import('@/pages/oficiosya/OficiosYa'))
const PerfilTecnico = lazy(() => import('@/pages/oficiosya/PerfilTecnico'))
const MenteResiliente = lazy(() => import('@/pages/menteresiliente/MenteResiliente'))
// Las de emergencia se precargan para que funcionen sin conexión (ver routes/paginas.js).
const Emergencia = lazy(cargarEmergencia)
const Reportar = lazy(cargarReportar)
const MisCasos = lazy(cargarMisCasos)
const DetalleCaso = lazy(cargarDetalleCaso)
const BandejaCasos = lazy(() => import('@/pages/casos/BandejaCasos'))
const MiPerfilTecnico = lazy(() => import('@/pages/oficiosya/MiPerfilTecnico'))
const Voluntariado = lazy(() => import('@/pages/voluntariado/Voluntariado'))
const AsignarVoluntarios = lazy(() => import('@/pages/voluntariado/AsignarVoluntarios'))
const Inspecciones = lazy(() => import('@/pages/inspeccion/Inspecciones'))
const NuevaInspeccion = lazy(() => import('@/pages/inspeccion/NuevaInspeccion'))
const Donar = lazy(() => import('@/pages/donaciones/Donar'))
const GestionDonaciones = lazy(() => import('@/pages/donaciones/GestionDonaciones'))
const Tablero = lazy(() => import('@/pages/admin/Tablero'))
const VerificarTecnicos = lazy(() => import('@/pages/admin/VerificarTecnicos'))
const Auditoria = lazy(() => import('@/pages/admin/Auditoria'))

export default function App() {
  return (
    <Suspense fallback={<PantallaCarga />}>
      <Routes>
        <Route path="/" element={<Inicio />} />

        {/* Solo sin sesión */}
        <Route element={<RutaPublica />}>
          <Route element={<LayoutAuth />}>
            <Route path="/login" element={<Login />} />
            <Route path="/registro" element={<Registro />} />
          </Route>
        </Route>

        {/* Con sesión (cualquier rol). Para limitar por rol: <RutaProtegida roles={[...]} /> */}
        <Route element={<RutaProtegida />}>
          <Route element={<LayoutPrincipal />}>
            <Route path="/panel" element={<Panel />} />

            {/* Modo Cotidiano (por ahora con datos de prueba: src/api/mocks) */}
            <Route path="/segundavida" element={<SegundaVida />} />
            <Route path="/segundavida/publicar" element={<Publicar />} />
            <Route path="/segundavida/:id" element={<DetallePublicacion />} />
            <Route path="/oficiosya" element={<OficiosYa />} />
            {/* Antes que /oficiosya/:id para que "mi-perfil" no se lea como un id */}
            <Route element={<RutaProtegida roles={[ROLES.TECNICO_VOLUNTARIO]} />}>
              <Route path="/oficiosya/mi-perfil" element={<MiPerfilTecnico />} />
              <Route path="/voluntariado" element={<Voluntariado />} />
            </Route>
            <Route path="/oficiosya/:id" element={<PerfilTecnico />} />
            <Route path="/mente-resiliente" element={<MenteResiliente />} />

            {/* Reportar y seguir los propios casos: ciudadanos, técnicos y profesionales (CU-29 a CU-32) */}
            <Route element={<RutaProtegida roles={ROLES_REPORTANTES} />}>
              {/* Reportar solo con la emergencia activa (CU-29 E3) */}
              <Route element={<RutaEmergencia />}>
                <Route path="/emergencia" element={<Emergencia />} />
                <Route path="/emergencia/reportar/:categoria" element={<Reportar />} />
              </Route>
              {/* Los casos se pueden consultar también después de la emergencia (CU-32) */}
              <Route path="/emergencia/casos" element={<MisCasos />} />
              <Route path="/emergencia/casos/:caseId" element={<DetalleCaso />} />
              {/* CU-33: ofrecer una donación */}
              <Route path="/donar" element={<Donar />} />
            </Route>

            {/* Bandeja de todos los casos: Inspector y Administrador (CU-39) */}
            <Route element={<RutaProtegida roles={ROLES_PERSONAL} />}>
              <Route path="/casos" element={<BandejaCasos />} />
              {/* Censo e inspección de inmuebles (CU-34 a CU-36) y voluntarios (CU-43) */}
              <Route path="/inspecciones" element={<Inspecciones />} />
              <Route path="/inspecciones/nueva" element={<NuevaInspeccion />} />
              <Route path="/voluntariado/asignar" element={<AsignarVoluntarios />} />
            </Route>

            {/* Solo Administrador: tablero, técnicos, donaciones y auditoría */}
            <Route element={<RutaProtegida roles={[ROLES.ADMINISTRADOR]} />}>
              <Route path="/admin/tablero" element={<Tablero />} />
              <Route path="/admin/tecnicos" element={<VerificarTecnicos />} />
              <Route path="/admin/auditoria" element={<Auditoria />} />
              <Route path="/donaciones" element={<GestionDonaciones />} />
            </Route>
          </Route>
        </Route>

        <Route path="/sin-permiso" element={<SinPermiso />} />
        <Route path="*" element={<NoEncontrado />} />
      </Routes>
    </Suspense>
  )
}
