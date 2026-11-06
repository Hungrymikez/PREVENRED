import {
  eliminarPendiente,
  guardarPendiente,
  listarPendientes,
  marcarError,
  reintentarPendiente,
} from './almacen'

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
    for (const p of await listarPendientes()) await eliminarPendiente(p.clientId)
  })

  it('guarda el reporte con un clientId único y lo recupera igual', async () => {
    const a = await guardarPendiente(reporte)
    const b = await guardarPendiente(reporte)
    expect(a.clientId).not.toBe(b.clientId)

    const [primero] = await listarPendientes()
    expect(primero.estado).toBe('pendiente')
    expect(primero.datos).toMatchObject(reporte)
  })

  it('guarda los datos cifrados, nunca en texto plano', async () => {
    await guardarPendiente(reporte)
    const [crudo] = await leerCrudo()
    const contenido = JSON.stringify(crudo) + new TextDecoder().decode(crudo.datos.datos)
    expect(contenido).not.toContain('Grieta grande')
  })

  it('conserva la foto', async () => {
    const foto = new Blob(['bytes-de-la-foto'], { type: 'image/jpeg' })
    await guardarPendiente({ ...reporte, foto })
    const [guardado] = await listarPendientes()
    expect(guardado.datos.foto.type).toBe('image/jpeg')
    expect(await guardado.datos.foto.text()).toBe('bytes-de-la-foto')
  })

  it('marca errores (E1) y permite reintentar', async () => {
    const { clientId } = await guardarPendiente(reporte)
    await marcarError(clientId, 'Datos inválidos')
    expect((await listarPendientes())[0]).toMatchObject({
      estado: 'error',
      error: 'Datos inválidos',
    })

    await reintentarPendiente(clientId)
    expect((await listarPendientes())[0]).toMatchObject({ estado: 'pendiente', error: null })
  })
})
