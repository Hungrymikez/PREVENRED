# PrevenRed · Frontend

Aplicación web adaptable a celular y tablero institucional de **PrevenRed**, plataforma digital de resiliencia urbana, economía colaborativa y bienestar comunitario para Pereira.

> Proyecto final de Economía Naranja y Desarrollo Sostenible · CIAF · Ingeniería en Análisis y Desarrollo de Software · 2026

---

## 1. ¿Qué hace este módulo?

El frontend es la interfaz que usan los cuatro tipos de usuario de PrevenRed. La plataforma funciona en dos modos que comparten usuarios, autenticación y datos:

| Modo           | Qué ve el usuario                                                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cotidiano**  | SegundaVida Pereira (materiales y herramientas), OficiosYa Pereira (técnicos verificados) y Mente Resiliente (bienestar emocional anónimo). |
| **Emergencia** | Reporte de incidentes georreferenciados, mapa multicapa, seguimiento del caso y movilización de recursos, técnicos y voluntarios.           |

La interfaz se reconfigura según el modo vigente (RF-01 y RF-02 de la especificación de requerimientos).

## 2. Roles y vistas

| Rol                             | Vistas principales                                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Ciudadano**                   | Inicio, SegundaVida, OficiosYa, Mente Resiliente, reportar incidente, seguimiento de mis reportes.                              |
| **Técnico / voluntario**        | Perfil verificado, portafolio, disponibilidad, asignaciones de apoyo.                                                           |
| **Inspector**                   | Formularios de campo, registro de evidencias (también sin conexión), asignaciones.                                              |
| **Coordinador / administrador** | Tablero institucional con mapa, validación y priorización de reportes, activación del Modo Emergencia, indicadores y auditoría. |

## 3. Stack tecnológico

- **React** + **Vite** (interfaz y servidor de desarrollo)
- **Tailwind CSS** (estilos utilitarios y diseño responsive, primero para celular)
- **React Router** (navegación)
- **React Hook Form + Zod** (formularios y validación)
- **Lucide** (íconos)
- **Prettier + Oxlint** (formato y revisión del código: `npm run format`, `npm run lint`)
- **Leaflet + OpenStreetMap** (mapas, sin costo de licencia)
- **Axios** (consumo de la API REST del backend) y **TanStack Query** (caché y estados de carga)
- **Vitest + Testing Library** (pruebas: `npm test`)

## 4. Requisitos

- Node.js 18 o superior
- npm 9 o superior
- Backend de PrevenRed corriendo (ver `README_backend.md`)

## 5. Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/Hungrymikez/PREVENRED.git
cd PREVENRED/frontEnd

# 2. Instalar dependencias
npm install

# 3. Configurar variables de entorno
cp .env.example .env

# 4. Levantar en desarrollo
npm run dev
```

La app queda en `http://localhost:5173`. En desarrollo, Vite reenvía las llamadas a `/api` al backend en `http://localhost:8000` (ver `vite.config.js`), así que el backend debe estar corriendo.

### Variables de entorno (`.env`)

```env
VITE_API_URL=/api/v1
VITE_MAP_CENTER_LAT=4.8133
VITE_MAP_CENTER_LNG=-75.6961
VITE_MAP_DEFAULT_ZOOM=13
```

> Las coordenadas corresponden al centro de Pereira. Ajusta el zoom según el sector.

### Scripts disponibles

| Comando           | Descripción                                                                |
| ----------------- | -------------------------------------------------------------------------- |
| `npm run dev`     | Servidor de desarrollo con recarga en caliente.                            |
| `npm run build`   | Compilación de producción en `dist/`.                                      |
| `npm run preview` | Previsualiza la compilación de producción.                                 |
| `npm run lint`    | Revisión de errores con Oxlint.                                            |
| `npm run format`  | Da formato al código con Prettier (también ordena las clases de Tailwind). |
| `npm test`        | Corre las pruebas una vez (`npm run test:watch` las repite al guardar).    |

## 6. Estructura sugerida del proyecto

```
frontEnd/
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

- [x] Registro y login (ciudadano o técnico/voluntario)
- [x] Rutas protegidas por rol
- [x] Layout responsive pensado primero para celular

**Etapa 2 · Modo Cotidiano**

> Las pantallas de esta etapa ya existen con **datos de prueba** (`src/api/mocks/`). Cuando el backend publique los endpoints, solo cambian las funciones de `src/api/segundavida.js`, `oficiosya.js` y `bienestar.js`.

- [x] SegundaVida: publicar, buscar, filtrar, intercambio, venta y alquiler _(datos de prueba; faltan fotos y solicitud de alquiler)_
- [x] OficiosYa: filtro por especialidad, zona, disponibilidad y valoración; lista y mapa; contacto por enlace autorizado de WhatsApp _(datos de prueba)_
- [ ] OficiosYa: calificar al técnico (RF-09) y pedir cotización (CU-20)
- [x] Mente Resiliente: consentimiento, registro anónimo de ánimo y líneas de apoyo _(datos de prueba; falta el número oficial de la línea)_

**Etapa 3 · Modo Emergencia**

> Base hecha con **datos de prueba** (`src/api/modo.js`, `src/api/incidentes.js`). En `npm run dev` aparece el botón "Demo: activar emergencia" para probar los dos modos.

- [x] Indicador visible del modo activo y reconfiguración de la interfaz (RF-02) _(datos de prueba)_
- [x] Formulario de reporte en 3 pasos: daño en vivienda, vía bloqueada y pedir ayuda, con ubicación por GPS o mapa, foto y descripción (RF-23) _(datos de prueba; la foto aún no se sube)_
- [ ] Mapa multicapa con Leaflet (RF-19, RF-25)
- [x] Seguimiento del caso por identificador único (RF-22) y estados: Reportado, En revisión, Asignado, En atención, Resuelto (RF-24)
- [ ] Tablero del coordinador: validar, priorizar, asignar recursos, técnicos y voluntarios (RF-27, RF-28)

**Etapa 4 · Pruebas y simulacro**

- [ ] Pruebas de usabilidad con usuarios reales
- [ ] Simulacro de activación y reporte

## 8. Accesibilidad y trabajo sin conexión

- Referencia de accesibilidad: **WCAG 2.1 AA** (RNF-09): contraste suficiente, navegación por teclado, etiquetas en formularios, textos alternativos.
- **Trabajo sin conexión** (CU-37, RNF-08). Implementado para los reportes de emergencia:
  - **PWA**: `public/sw.js` guarda la app para que abra sin señal y `public/manifest.webmanifest` permite instalarla. Solo se activa en producción (`npm run build`); en `npm run dev` no.
  - Sin señal, el reporte se guarda en el celular (**IndexedDB, cifrado con AES-GCM**) con un `clientId` único, para que el servidor nunca lo duplique (`src/offline/almacen.js`).
  - Al volver la señal se envían solos, en orden, y se reintenta cada 30 s (`src/offline/sincronizar.js`). Si el servidor rechaza uno, queda marcado en _Mis casos_ para reintentar o descartar.
  - Sin señal se usan el último usuario y el último modo conocidos, para poder reportar aunque la app abra sin conexión.
  - **Pendiente**: guardar el mapa base para verlo sin señal (hoy sin red se ve vacío, pero el GPS y tocar el mapa siguen funcionando) y priorizar el envío por gravedad.
  - **Para probarlo**: `npm run build` y `npm run preview`, luego en Chrome DevTools → _Network_ → _Offline_.

## 9. Convenciones de trabajo

- Metodología **Scrum**, con entregas incrementales.
- Roles del equipo: frontend, backend y base de datos.
- Ramas: `main` (estable) y una rama por tarea creada desde `main`, con prefijo según el tipo de cambio:
  - `feat/` nueva funcionalidad · ej. `feat/login-con-google`
  - `fix/` corrección de un error · ej. `fix/boton-enviar-duplicado`
  - `hotfix/` arreglo urgente en producción · ej. `hotfix/caida-checkout-pagos`
  - `refactor/` mejora de código sin cambiar el comportamiento · ej. `refactor/limpieza-componente-tabla`
  - `docs/` solo documentación · ej. `docs/actualizar-readme`
  - `chore/` mantenimiento, dependencias o configuración · ej. `chore/actualizar-paquetes-npm`
  - `test/` pruebas · ej. `test/unitarias-modulo-auth`
- Commits en español, cortos y claros. Ejemplo: `feat: formulario de reporte de incidente`.
- Todo cambio entra por _pull request_ con al menos una revisión.

## 10. Decisiones pendientes

- Si la asignación de reportes en emergencia será **automática por ubicación** o requerirá **aprobación del coordinador**. Esto cambia el flujo del tablero.

## 11. Equipo

Sofía Jaramillo · Sara Salas · Juan Camilo Mosquera · Daniel García · Andrés Jiménez · Michael Zuluaga

Docente: Geraldine Toro · CIAF · Pereira, 2026
