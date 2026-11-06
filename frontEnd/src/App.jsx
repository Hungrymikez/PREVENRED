import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router'
import { PantallaCarga } from '@/components/ui/PantallaCarga'
import { LayoutAuth } from '@/layouts/LayoutAuth'
import { LayoutPrincipal } from '@/layouts/LayoutPrincipal'
import Inicio from '@/pages/Inicio'
import { NoEncontrado, SinPermiso } from '@/pages/PaginaMensaje'
import { RutaProtegida, RutaPublica } from '@/routes/RutaProtegida'

// Cada página se descarga solo cuando se visita (la app abre más rápido, sobre todo en celular).
const Login = lazy(() => import('@/pages/auth/Login'))
const Registro = lazy(() => import('@/pages/auth/Registro'))
const Panel = lazy(() => import('@/pages/Panel'))
const SegundaVida = lazy(() => import('@/pages/segundavida/SegundaVida'))
const DetallePublicacion = lazy(() => import('@/pages/segundavida/DetallePublicacion'))
const Publicar = lazy(() => import('@/pages/segundavida/Publicar'))
const OficiosYa = lazy(() => import('@/pages/oficiosya/OficiosYa'))
const PerfilTecnico = lazy(() => import('@/pages/oficiosya/PerfilTecnico'))
const MenteResiliente = lazy(() => import('@/pages/menteresiliente/MenteResiliente'))

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
            <Route path="/oficiosya/:id" element={<PerfilTecnico />} />
            <Route path="/mente-resiliente" element={<MenteResiliente />} />
          </Route>
        </Route>

        <Route path="/sin-permiso" element={<SinPermiso />} />
        <Route path="*" element={<NoEncontrado />} />
      </Routes>
    </Suspense>
  )
}
