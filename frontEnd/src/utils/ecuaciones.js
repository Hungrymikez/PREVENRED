/**
 * Modelos con ecuaciones diferenciales ordinarias (EDO) de primer orden que usa la app.
 * Se resuelven de forma analítica (solución exacta), así la interfaz solo evalúa fórmulas.
 *
 * 1) Casos pendientes (Tablero municipal):
 *      dB/dt = λ − μ·B ,  B(0) = B₀
 *    λ = reportes nuevos por hora, μ = fracción de casos pendientes que se atienden por hora.
 *    Es lineal: con factor integrante e^(μt) queda
 *      B(t) = λ/μ + (B₀ − λ/μ)·e^(−μt)
 *    y B(t) tiende al equilibrio λ/μ (donde dB/dt = 0).
 *
 * 2) Llegada del técnico (OficiosYa):
 *      dv/dt = (v_máx − v)/τ ,  v(0) = 0
 *    El técnico arranca quieto y se acerca a la velocidad de la vía v_máx; τ es el tiempo
 *    que tarda en "tomar ritmo" (salir del barrio, semáforos). Separando variables:
 *      v(t) = v_máx·(1 − e^(−t/τ))
 *    e integrando la velocidad (x(0) = 0):
 *      x(t) = v_máx·[t − τ·(1 − e^(−t/τ))]
 */

/** Fracción de los casos pendientes que atiende un inspector por hora (5 %). */
export const ATENCION_POR_INSPECTOR = 0.05

/** μ total: cada inspector suma su capacidad de atención. */
export function tasaAtencion(inspectores) {
  return inspectores * ATENCION_POR_INSPECTOR
}

/** Solución B(t) de dB/dt = λ − μB. Con μ = 0 nadie atiende: B crece en línea recta. */
export function pendientesEn(t, { inicial, llegada, atencion }) {
  if (atencion <= 0) return inicial + llegada * t
  const equilibrio = llegada / atencion
  return equilibrio + (inicial - equilibrio) * Math.exp(-atencion * t)
}

/** Punto de equilibrio λ/μ (Infinity si nadie atiende). */
export function equilibrioPendientes({ llegada, atencion }) {
  return atencion > 0 ? llegada / atencion : Infinity
}

/**
 * Horas para que los pendientes bajen (o suban) hasta `meta`, despejando t de B(t) = meta:
 *   t = −ln((meta − λ/μ) / (B₀ − λ/μ)) / μ
 * Devuelve null si la curva nunca alcanza la meta (queda del otro lado del equilibrio).
 */
export function horasHastaPendientes(meta, { inicial, llegada, atencion }) {
  if (atencion <= 0) return null
  const equilibrio = llegada / atencion
  const cociente = (meta - equilibrio) / (inicial - equilibrio)
  if (!(cociente > 0 && cociente <= 1)) return null
  return -Math.log(cociente) / atencion
}

/**
 * Reportes por hora (λ) con los casos creados en las últimas `horas` horas.
 * `ahora` se recibe para poder probarla con una fecha fija.
 */
export function reportesPorHora(casos, { horas = 24, ahora = Date.now() } = {}) {
  const desde = ahora - horas * 3_600_000
  const recientes = casos.filter((c) => new Date(c.created_at).getTime() >= desde).length
  return recientes / horas
}

/** Velocidad máxima (km/h) y tiempo de arranque τ (minutos) según el modo de la ciudad. */
export const CONDICIONES_VIA = {
  COTIDIANO: { velocidadMax: 30, arranqueMin: 3 },
  EMERGENCIA: { velocidadMax: 15, arranqueMin: 6 },
}

/**
 * Las calles no van en línea recta: la distancia de Haversine se multiplica por este factor
 * para aproximar la distancia real por vías.
 */
export const FACTOR_RUTA = 1.3

/** v(t) en km/h, con t en minutos. */
export function velocidadEn(tMin, { velocidadMax, arranqueMin }) {
  return velocidadMax * (1 - Math.exp(-tMin / arranqueMin))
}

/** x(t) en km recorridos, con t en minutos. */
export function recorridoEn(tMin, { velocidadMax, arranqueMin }) {
  const t = tMin / 60
  const tau = arranqueMin / 60
  return velocidadMax * (t - tau * (1 - Math.exp(-t / tau)))
}

/**
 * Minutos para recorrer `km`: se despeja t de x(t) = km. No tiene despeje con funciones
 * elementales, así que se resuelve con el método de bisección (x(t) es creciente).
 */
export function minutosDeLlegada(km, condiciones) {
  if (km <= 0) return 0
  let bajo = 0
  let alto = 1
  while (recorridoEn(alto, condiciones) < km) alto *= 2
  for (let i = 0; i < 60; i++) {
    const medio = (bajo + alto) / 2
    if (recorridoEn(medio, condiciones) < km) bajo = medio
    else alto = medio
  }
  return (bajo + alto) / 2
}
