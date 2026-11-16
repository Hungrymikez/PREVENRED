/**
 * Tablero del Administrador. Conectado al backend real (todas las rutas exigen rol administrador):
 * - CU-45 Tablero municipal: GET /reporting/dashboard
 * - CU-26 Indicadores de bienestar por barrio: GET /wellbeing/indicators
 * - CU-46 Exportar incidentes: GET /reporting/export/incidents/csv
 * - CU-09 Auditoría: GET /audit/logs
 */
import { api } from '@/api/client'

/** CU-45. Totales de incidentes, inspecciones, ayudas y voluntariado. */
export async function obtenerTablero() {
  const { data } = await api.get('/reporting/dashboard')
  return data
}

/**
 * CU-26. Promedio de ánimo por barrio. El backend solo publica barrios con 3 o más respuestas
 * (k-anonimato, RF-17), así que nunca llegan datos individuales.
 */
export async function obtenerIndicadoresBienestar() {
  const { data } = await api.get('/wellbeing/indicators')
  return data
}

/** CU-46. El backend devuelve { filename, csv_content }; aquí solo se pide. */
export async function exportarIncidentesCsv() {
  const { data } = await api.get('/reporting/export/incidents/csv')
  return data
}

/** Descarga en el navegador un texto CSV como archivo. */
export function descargarCsv({ filename, csv_content: contenido }) {
  // El BOM hace que Excel lea bien las tildes y la ñ.
  const archivo = new Blob(['﻿', contenido], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(archivo)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = filename || 'prevenred_incidentes.csv'
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(url)
}

/** CU-46. Pide el CSV y lo descarga. Devuelve el nombre del archivo. */
export async function descargarIncidentesCsv() {
  const exportacion = await exportarIncidentesCsv()
  descargarCsv(exportacion)
  return exportacion.filename
}

/** CU-09. Registros de auditoría, más recientes primero. `recurso` filtra (p. ej. "incidents"). */
export async function listarAuditoria({ recurso, limite = 50 } = {}) {
  const params = { limit: limite }
  if (recurso) params.resource = recurso
  const { data } = await api.get('/audit/logs', { params })
  return data
}
