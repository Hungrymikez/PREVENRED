import {
  eliminarPendiente,
  guardarPendiente,
  listarPendientes,
  marcarError,
  reintentarPendiente,
} from './almacen'

const ANA = 'u-ana'
const BETO = 'u-beto'

const reporte = {
  categoria: 'vivienda',
  type: 'GRIETAS',
  description: 'Grieta grande en la pared de la cocina',
  quantity: '1',
  coordenadas: [4.81, -75.69],
}

/** Lee lo que quedó guardado tal cual en IndexedDB, sin descifrar. */
function leerCrudo() {
  return new Promise((resolver) => {
    const peticion = indexedDB.open('prevenred-offline')
    peticion.onsuccess = () => {
      const db = peticion.result
      const lectura = db.transaction('pendientes').objectStore('pendientes').getAll()
      lectura.onsuccess = () => {
        db.close()
        resolver(lectura.result)
      }
    }
  })
}

describe('almacén sin conexión (CU-37)', () => {
  afterEach(async () => {
    for (const usuario of [ANA, BETO]) {
      for (const p of await listarPendientes(usuario)) await eliminarPendiente(p.clientId)
    }
  })

  it('guarda el reporte con un clientId único y lo recupera igual', async () => {
    const a = await guardarPendiente(reporte, ANA)
    const b = await guardarPendiente(reporte, ANA)
    expect(a.clientId).not.toBe(b.clientId)

    const [primero] = await listarPendientes(ANA)
    expect(primero.estado).toBe('pendiente')
    expect(primero.datos).toMatchObject(reporte)
  })

  it('guarda los datos cifrados, nunca en texto plano', async () => {
    await guardarPendiente(reporte, ANA)
    const [crudo] = await leerCrudo()
    const contenido = JSON.stringify(crudo) + new TextDecoder().decode(crudo.datos.datos)
    expect(contenido).not.toContain('Grieta grande')
  })

  it('conserva la foto', async () => {
    const foto = new Blob(['bytes-de-la-foto'], { type: 'image/jpeg' })
    await guardarPendiente({ ...reporte, foto }, ANA)
    const [guardado] = await listarPendientes(ANA)
    expect(guardado.datos.foto.type).toBe('image/jpeg')
    expect(await guardado.datos.foto.text()).toBe('bytes-de-la-foto')
  })

  it('marca errores (E1) y permite reintentar', async () => {
    const { clientId } = await guardarPendiente(reporte, ANA)
    await marcarError(clientId, 'Datos inválidos')
    expect((await listarPendientes(ANA))[0]).toMatchObject({
      estado: 'error',
      error: 'Datos inválidos',
    })

    await reintentarPendiente(clientId)
    expect((await listarPendientes(ANA))[0]).toMatchObject({ estado: 'pendiente', error: null })
  })

  it('cada persona solo ve sus propios reportes (celular compartido)', async () => {
    const deAna = await guardarPendiente(reporte, ANA)
    const deBeto = await guardarPendiente({ ...reporte, description: 'Reporte de Beto' }, BETO)

    expect((await listarPendientes(ANA)).map((p) => p.clientId)).toEqual([deAna.clientId])
    expect((await listarPendientes(BETO)).map((p) => p.clientId)).toEqual([deBeto.clientId])
  })

  it('no ofrece a nadie los reportes sin dueño de versiones anteriores', async () => {
    await new Promise((resolver) => {
      const peticion = indexedDB.open('prevenred-offline')
      peticion.onsuccess = () => {
        const db = peticion.result
        const tx = db.transaction('pendientes', 'readwrite')
        tx.objectStore('pendientes').put({ clientId: 'viejo', creadoEn: '2026-01-01' })
        tx.oncomplete = () => {
          db.close()
          resolver()
        }
      }
    })
    expect(await listarPendientes(ANA)).toEqual([])
    await eliminarPendiente('viejo')
  })

  it('exige saber de quién es el reporte', async () => {
    await expect(guardarPendiente(reporte)).rejects.toThrow('usuario')
    await expect(listarPendientes()).rejects.toThrow('usuario')
  })
})
