/**
 * Almacén local de reportes hechos sin conexión (CU-37).
 * - Se guardan en IndexedDB, cifrados con AES-GCM. La clave se crea en el dispositivo
 *   y no se puede exportar: solo esta app, en este navegador, puede descifrarlos.
 * - Cada reporte lleva un clientId único: el servidor lo usa para no duplicarlo (H-07).
 * - Al sincronizar, la copia local se elimina.
 */

const BASE = 'prevenred-offline'
const VERSION = 1
const ESPACIO_MINIMO_BYTES = 5 * 1024 * 1024

function abrir() {
  return new Promise((resolver, rechazar) => {
    const peticion = indexedDB.open(BASE, VERSION)
    peticion.onupgradeneeded = () => {
      const db = peticion.result
      db.createObjectStore('claves')
      db.createObjectStore('pendientes', { keyPath: 'clientId' })
    }
    peticion.onsuccess = () => resolver(peticion.result)
    peticion.onerror = () => rechazar(peticion.error)
  })
}

/** Ejecuta una operación sobre un almacén y espera a que la transacción termine. */
async function operar(almacen, modo, accion) {
  const db = await abrir()
  try {
    return await new Promise((resolver, rechazar) => {
      const transaccion = db.transaction(almacen, modo)
      const peticion = accion(transaccion.objectStore(almacen))
      transaccion.oncomplete = () => resolver(peticion?.result)
      transaccion.onerror = () => rechazar(transaccion.error)
    })
  } finally {
    db.close()
  }
}

async function obtenerClave() {
  const guardada = await operar('claves', 'readonly', (s) => s.get('principal'))
  if (guardada) return guardada
  const clave = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, [
    'encrypt',
    'decrypt',
  ])
  await operar('claves', 'readwrite', (s) => s.put(clave, 'principal'))
  return clave
}

async function cifrar(clave, bytes) {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const datos = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, clave, bytes)
  return { iv, datos }
}

function descifrar(clave, { iv, datos }) {
  return crypto.subtle.decrypt({ name: 'AES-GCM', iv }, clave, datos)
}

/** E2: avisa si el dispositivo casi no tiene espacio antes de guardar. */
export async function hayEspacio() {
  if (!navigator.storage?.estimate) return true
  const { quota = Infinity, usage = 0 } = await navigator.storage.estimate()
  return quota - usage > ESPACIO_MINIMO_BYTES
}

/** Guarda un reporte cifrado y devuelve su resumen { clientId, creadoEn }. */
export async function guardarPendiente({ foto, ...datos }) {
  const clave = await obtenerClave()
  const texto = new TextEncoder().encode(JSON.stringify(datos))
  const registro = {
    clientId: crypto.randomUUID(),
    creadoEn: new Date().toISOString(),
    estado: 'pendiente',
    error: null,
    datos: await cifrar(clave, texto),
    foto: foto ? await cifrar(clave, await foto.arrayBuffer()) : null,
    fotoTipo: foto?.type ?? null,
  }
  await operar('pendientes', 'readwrite', (s) => s.put(registro))
  return { clientId: registro.clientId, creadoEn: registro.creadoEn }
}

/** Devuelve los pendientes ya descifrados, del más antiguo al más reciente. */
export async function listarPendientes() {
  const registros = await operar('pendientes', 'readonly', (s) => s.getAll())
  if (!registros?.length) return []
  const clave = await obtenerClave()

  const pendientes = await Promise.all(
    registros.map(async (r) => {
      const datos = JSON.parse(new TextDecoder().decode(await descifrar(clave, r.datos)))
      const foto = r.foto ? new Blob([await descifrar(clave, r.foto)], { type: r.fotoTipo }) : null
      return {
        clientId: r.clientId,
        creadoEn: r.creadoEn,
        estado: r.estado,
        error: r.error,
        datos: { ...datos, foto },
      }
    }),
  )
  return pendientes.sort((a, b) => a.creadoEn.localeCompare(b.creadoEn))
}

export function eliminarPendiente(clientId) {
  return operar('pendientes', 'readwrite', (s) => s.delete(clientId))
}

async function cambiarEstado(clientId, estado, error) {
  const registro = await operar('pendientes', 'readonly', (s) => s.get(clientId))
  if (!registro) return
  await operar('pendientes', 'readwrite', (s) => s.put({ ...registro, estado, error }))
}

/** E1: el servidor lo rechazó. Se conserva para que la persona lo revise. */
export function marcarError(clientId, mensaje) {
  return cambiarEstado(clientId, 'error', mensaje)
}

export function reintentarPendiente(clientId) {
  return cambiarEstado(clientId, 'pendiente', null)
}
