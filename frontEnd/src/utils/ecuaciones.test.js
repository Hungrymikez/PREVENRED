import {
  CONDICIONES_VIA,
  equilibrioPendientes,
  horasHastaPendientes,
  minutosDeLlegada,
  pendientesEn,
  recorridoEn,
  reportesPorHora,
  tasaAtencion,
  velocidadEn,
} from './ecuaciones'

const MODELO = { inicial: 45, llegada: 12, atencion: tasaAtencion(4) } // μ = 0,2

describe('casos pendientes: dB/dt = λ − μB', () => {
  it('cumple la condición inicial B(0) = B₀', () => {
    expect(pendientesEn(0, MODELO)).toBeCloseTo(45)
  })

  it('se acerca al equilibrio λ/μ', () => {
    expect(equilibrioPendientes(MODELO)).toBeCloseTo(60)
    expect(pendientesEn(100, MODELO)).toBeCloseTo(60, 3)
  })

  it('satisface la ecuación diferencial (derivada numérica)', () => {
    const t = 3
    const h = 1e-5
    const derivada = (pendientesEn(t + h, MODELO) - pendientesEn(t - h, MODELO)) / (2 * h)
    expect(derivada).toBeCloseTo(MODELO.llegada - MODELO.atencion * pendientesEn(t, MODELO), 4)
  })

  it('despeja el tiempo para llegar a una meta', () => {
    const conMasInspectores = { ...MODELO, atencion: tasaAtencion(10) } // equilibrio 24
    const t = horasHastaPendientes(30, conMasInspectores)
    expect(pendientesEn(t, conMasInspectores)).toBeCloseTo(30)
    expect(horasHastaPendientes(20, conMasInspectores)).toBeNull() // por debajo del equilibrio
  })

  it('sin inspectores los casos solo se acumulan', () => {
    expect(pendientesEn(10, { ...MODELO, atencion: 0 })).toBe(45 + 120)
    expect(equilibrioPendientes({ llegada: 12, atencion: 0 })).toBe(Infinity)
  })

  it('estima λ con los casos de las últimas 24 horas', () => {
    const ahora = new Date('2026-11-18T12:00:00Z').getTime()
    const casos = [
      { created_at: '2026-11-18T10:00:00Z' },
      { created_at: '2026-11-17T13:00:00Z' },
      { created_at: '2026-11-10T10:00:00Z' },
    ]
    expect(reportesPorHora(casos, { ahora })).toBeCloseTo(2 / 24)
  })
})

describe('llegada del técnico: dv/dt = (v_máx − v)/τ', () => {
  const via = CONDICIONES_VIA.COTIDIANO

  it('arranca quieto y se acerca a la velocidad máxima', () => {
    expect(velocidadEn(0, via)).toBe(0)
    expect(velocidadEn(60, via)).toBeCloseTo(30, 3)
  })

  it('el recorrido es la integral de la velocidad', () => {
    const t = 5
    const h = 1e-4
    const derivadaKmPorMin = (recorridoEn(t + h, via) - recorridoEn(t - h, via)) / (2 * h)
    expect(derivadaKmPorMin * 60).toBeCloseTo(velocidadEn(t, via), 3)
  })

  it('despeja el tiempo de llegada y tarda más en emergencia', () => {
    const minutos = minutosDeLlegada(6, via)
    expect(recorridoEn(minutos, via)).toBeCloseTo(6, 6)
    // A 30 km/h sin arranque serían 12 min; el arranque suma unos τ = 3 min.
    expect(minutos).toBeCloseTo(15, 0)
    // Mitad de velocidad y doble arranque: la solución escala y tarda justo el doble.
    expect(minutosDeLlegada(6, CONDICIONES_VIA.EMERGENCIA)).toBeCloseTo(minutos * 2, 6)
    expect(minutosDeLlegada(0, via)).toBe(0)
  })
})
