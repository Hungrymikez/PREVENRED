/**
 * Service worker de PrevenRed: permite abrir la app sin conexión (RNF-08).
 * - Páginas: primero la red; sin red, la última versión guardada.
 * - Archivos de /assets (JS, CSS, imágenes): se guardan la primera vez que se usan.
 *   Sus nombres cambian en cada versión, así que nunca quedan desactualizados.
 * - La API (/api) nunca se guarda aquí: los reportes sin conexión los maneja la app (CU-37).
 */
const CACHE = 'prevenred-v1'
const BASICOS = ['/', '/index.html', '/favicon.svg', '/manifest.webmanifest']

self.addEventListener('install', (evento) => {
  evento.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(BASICOS)))
  self.skipWaiting()
})

self.addEventListener('activate', (evento) => {
  // Borra las versiones anteriores del caché.
  evento.waitUntil(
    caches
      .keys()
      .then((nombres) =>
        Promise.all(nombres.filter((n) => n !== CACHE).map((n) => caches.delete(n))),
      )
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (evento) => {
  const { request } = evento
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    evento.respondWith(
      fetch(request)
        .then((respuesta) => {
          const copia = respuesta.clone()
          caches.open(CACHE).then((cache) => cache.put('/index.html', copia))
          return respuesta
        })
        .catch(() => caches.match('/index.html')),
    )
    return
  }

  if (url.pathname.startsWith('/assets/')) {
    evento.respondWith(
      caches.match(request).then(
        (guardada) =>
          guardada ??
          fetch(request).then((respuesta) => {
            const copia = respuesta.clone()
            caches.open(CACHE).then((cache) => cache.put(request, copia))
            return respuesta
          }),
      ),
    )
  }
})
