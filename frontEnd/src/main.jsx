import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { queryClient } from '@/api/queryClient'
import App from '@/App'
import { AuthProvider } from '@/context/AuthProvider'
import { precargarModoEmergencia } from '@/routes/paginas'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)

// Solo en producción (npm run build): en desarrollo el caché estorbaría al editar.
// Se registra el service worker y se precargan las pantallas de emergencia,
// para que la app abra y permita reportar sin conexión (RNF-08).
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then(() => navigator.serviceWorker.ready)
      .then(precargarModoEmergencia)
      .catch(() => {
        // Sin service worker la app funciona igual, solo que no abre sin conexión.
      })
  })
}
