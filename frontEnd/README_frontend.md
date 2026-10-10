# PrevenRed · Frontend

Aplicación web adaptable a celular y tablero institucional de **PrevenRed**, plataforma digital de resiliencia urbana, economía colaborativa y bienestar comunitario para Pereira.

> Proyecto final de Economía Naranja y Desarrollo Sostenible · CIAF · Ingeniería en Análisis y Desarrollo de Software · 2026

---

## 1. ¿Qué hace este módulo?

El frontend es la interfaz que usan los cuatro tipos de usuario de PrevenRed. La plataforma funciona en dos modos que comparten usuarios, autenticación y datos:

| Modo | Qué ve el usuario |
| --- | --- |
| **Cotidiano** | SegundaVida Pereira (materiales y herramientas), OficiosYa Pereira (técnicos verificados) y Mente Resiliente (bienestar emocional anónimo). |
| **Emergencia** | Reporte de incidentes georreferenciados, mapa multicapa, seguimiento del caso y movilización de recursos, técnicos y voluntarios. |

La interfaz se reconfigura según el modo vigente (RF-01 y RF-02 de la especificación de requerimientos).

## 2. Roles y vistas

| Rol | Vistas principales |
| --- | --- |
| **Ciudadano** | Inicio, SegundaVida, OficiosYa, Mente Resiliente, reportar incidente, seguimiento de mis reportes. |
| **Técnico / voluntario** | Perfil verificado, portafolio, disponibilidad, asignaciones de apoyo. |
| **Inspector** | Formularios de campo, registro de evidencias (también sin conexión), asignaciones. |
| **Coordinador / administrador** | Tablero institucional con mapa, validación y priorización de reportes, activación del Modo Emergencia, indicadores y auditoría. |

## 3. Stack tecnológico

- **React** (interfaz) y **Bootstrap** (estilos y componentes responsive)
- **React Router** (navegación)
- **Leaflet + OpenStreetMap** (mapas, sin costo de licencia)
- **Axios** o `fetch` (consumo de la API REST del backend)

## 4. Requisitos

- Node.js 18 o superior
- npm 9 o superior
- Backend de PrevenRed corriendo (ver `README_backend.md`)

## 5. Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd prevenred/frontend

# 2. Instalar dependencias
npm install

# 3. Configurar variables de entorno
cp .env.example .env

# 4. Levantar en desarrollo
npm run dev
```

Por defecto la app queda en `http://localhost:5173` (si el proyecto se crea con Vite).

### Variables de entorno (`.env`)

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_MAP_CENTER_LAT=4.8133
VITE_MAP_CENTER_LNG=-75.6961
VITE_MAP_DEFAULT_ZOOM=13
```

> Las coordenadas corresponden al centro de Pereira. Ajusta el zoom según el sector.

### Scripts disponibles

| Comando | Descripción |
| --- | --- |
| `npm run dev` | Servidor de desarrollo con recarga en caliente. |
| `npm run build` | Compilación de producción en `dist/`. |
| `npm run preview` | Previsualiza la compilación de producción. |
| `npm run lint` | Revisión de estilo y errores con ESLint. |

## 6. Estructura sugerida del proyecto

```
frontend/
├── public/
├── src/
│   ├── api/              # Cliente HTTP y llamadas por recurso
│   ├── assets/
│   ├── components/       # Componentes reutilizables (botones, tarjetas, mapa)
│   ├── context/          # Autenticación y modo de la plataforma (cotidiano/emergencia)
│   ├── hooks/
│   ├── layouts/          # Layouts por rol
│   ├── pages/
│   │   ├── auth/         # Registro e inicio de sesión
│   │   ├── segundavida/
│   │   ├── oficiosya/
│   │   ├── menteresiliente/
│   │   ├── emergencia/   # Reportes, mapa multicapa, seguimiento
│   │   └── tablero/      # Vista institucional (coordinador)
│   ├── routes/           # Rutas protegidas por rol
│   ├── utils/
│   ├── App.jsx
│   └── main.jsx
├── .env.example
└── package.json
```

## 7. Funcionalidades a construir (por etapas)

Siguen las etapas de la especificación: levantamiento y arquitectura, Modo Cotidiano, Modo Emergencia, pruebas y simulacro, puesta en operación.

**Etapa 1 · Base**
- [ ] Registro y login (ciudadano o técnico/voluntario)
- [ ] Rutas protegidas por rol
- [ ] Layout responsive pensado primero para celular

**Etapa 2 · Modo Cotidiano**
- [ ] SegundaVida: publicar, buscar, filtrar, intercambio, venta y alquiler
- [ ] OficiosYa: filtro por especialidad, zona, disponibilidad y valoración; lista y mapa; contacto por enlace autorizado de WhatsApp; calificación (RF-09)
- [ ] Mente Resiliente: participación anónima

**Etapa 3 · Modo Emergencia**
- [ ] Indicador visible del modo activo y reconfiguración de la interfaz (RF-02)
- [ ] Formulario de reporte: ubicación, foto y descripción (RF-23)
- [ ] Mapa multicapa con Leaflet (RF-19, RF-25)
- [ ] Seguimiento del caso por identificador único (RF-22) y estados: Reportado, En revisión, Asignado, En atención, Resuelto (RF-24)
- [ ] Tablero del coordinador: validar, priorizar, asignar recursos, técnicos y voluntarios (RF-27, RF-28)

**Etapa 4 · Pruebas y simulacro**
- [ ] Pruebas de usabilidad con usuarios reales
- [ ] Simulacro de activación y reporte

## 8. Accesibilidad y trabajo sin conexión

- Referencia de accesibilidad: **WCAG 2.1 AA** (RNF-09): contraste suficiente, navegación por teclado, etiquetas en formularios, textos alternativos.
- Enfoque **offline-first** (propuesta de implementación, a validar con el equipo):
  - Convertir la app en **PWA** con *service worker* para guardar la interfaz y datos básicos.
  - Guardar los reportes en el dispositivo (IndexedDB) con un identificador generado localmente.
  - Enviar la cola de reportes automáticamente al recuperar conexión, priorizando gravedad alta.
  - Precargar capas del mapa y datos de la zona durante el uso cotidiano.

## 9. Convenciones de trabajo

- Metodología **Scrum**, con entregas incrementales.
- Roles del equipo: frontend, backend y base de datos.
- Ramas: `main` (estable), `develop` (integración) y `feature/<nombre>` por tarea.
- Commits en español, cortos y claros. Ejemplo: `feat: formulario de reporte de incidente`.
- Todo cambio entra por *pull request* con al menos una revisión.

## 10. Decisiones pendientes

- Si la asignación de reportes en emergencia será **automática por ubicación** o requerirá **aprobación del coordinador**. Esto cambia el flujo del tablero.

## 11. Equipo

Sofía Jaramillo · Sara Salas · Juan Camilo Mosquera · Daniel García · Andrés Jiménez · Michael Zuluaga

Docente: Geraldine Toro · CIAF · Pereira, 2026
