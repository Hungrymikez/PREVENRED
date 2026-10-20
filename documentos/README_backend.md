# PrevenRed · Backend

API REST de **PrevenRed**, plataforma digital de resiliencia urbana, economía colaborativa y bienestar comunitario para Pereira.

> Proyecto final de Economía Naranja y Desarrollo Sostenible · CIAF · Ingeniería en Análisis y Desarrollo de Software · 2026

---

## 1. ¿Qué hace este módulo?

El backend centraliza la lógica, la seguridad y los datos de la plataforma. Atiende al frontend mediante una **API REST** y soporta los dos modos de funcionamiento:

- **Modo Cotidiano:** SegundaVida (publicaciones de materiales y herramientas), OficiosYa (técnicos verificados) y Mente Resiliente (participación anónima y análisis NLP).
- **Modo Emergencia:** reportes georreferenciados, validación, asignación de recursos, técnicos y voluntarios, y auditoría de cada cambio.

Un administrador autorizado de la Alcaldía o la DIGER activa y desactiva el Modo Emergencia (RF-01). Mientras está activo se suspenden comisiones y planes de visibilidad.

## 2. Stack tecnológico

- **Python 3.11+** con **FastAPI**
- **MongoDB** como base de datos
- **Motor** (driver asíncrono) o **Beanie** (ODM) para acceder a MongoDB
- **Pydantic** para validar datos
- **JWT** para autenticación y **RBAC** para control de acceso por rol
- **Uvicorn** como servidor ASGI
- **Pytest** para pruebas

## 3. Requisitos

- Python 3.11 o superior
- MongoDB 6 o superior (local o en MongoDB Atlas)
- `pip` y `venv`

## 4. Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd prevenred/backend

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env

# 5. Levantar el servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

La documentación interactiva de la API queda disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Variables de entorno (`.env`)

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=prevenred
JWT_SECRET=cambia_esto_por_un_secreto_largo
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173
```

> Nunca subas el archivo `.env` al repositorio. Agrégalo al `.gitignore` y comparte solo `.env.example`.

## 5. Estructura sugerida del proyecto

```
backend/
├── app/
│   ├── main.py              # Punto de entrada de FastAPI
│   ├── core/                # Configuración, seguridad (JWT, hash), dependencias
│   ├── db/                  # Conexión a MongoDB e índices
│   ├── models/              # Modelos de documentos
│   ├── schemas/             # Esquemas Pydantic (entrada y salida)
│   ├── routers/
│   │   ├── auth.py
│   │   ├── usuarios.py
│   │   ├── segundavida.py
│   │   ├── oficiosya.py
│   │   ├── menteresiliente.py
│   │   ├── emergencia.py    # Activación del modo, reportes, asignaciones
│   │   └── auditoria.py
│   ├── services/            # Lógica de negocio
│   └── utils/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## 6. Roles y permisos (RBAC)

| Rol | Puede |
| --- | --- |
| **Ciudadano** | Usar SegundaVida, OficiosYa y Mente Resiliente; crear reportes y consultar los suyos. |
| **Técnico / voluntario** | Gestionar su perfil verificado; recibir asignaciones según especialidad, ubicación y disponibilidad. |
| **Inspector** | Registrar inspecciones y evidencias; consultar asignaciones. |
| **Coordinador / administrador** | Activar o desactivar el Modo Emergencia, validar y priorizar reportes, asignar recursos, ver auditoría. |

Los datos sensibles solo se exponen al rol autorizado.

## 7. Colecciones principales (MongoDB)

| Colección | Contenido |
| --- | --- |
| `usuarios` | Cuenta, rol, perfil, estado de verificación (técnicos). |
| `publicaciones` | Materiales y herramientas de SegundaVida: intercambio, venta o alquiler. |
| `tecnicos` | Especialidad, zona, disponibilidad, portafolio, calificaciones y plan de visibilidad. |
| `calificaciones` | Valoraciones que alimentan la reputación comunitaria (RF-09). |
| `participaciones_bienestar` | Entradas anónimas de Mente Resiliente y resultados agregados del NLP. |
| `reportes` | Incidentes: ubicación, tipo, gravedad, necesidades, evidencia, estado e identificador único. |
| `asignaciones` | Recursos, técnicos y voluntarios asignados a un reporte. |
| `estado_plataforma` | Modo vigente (cotidiano o emergencia) y quién lo activó. |
| `auditoria` | Registro de cada cambio relevante (RF-05). |

**Índice geoespacial:** los campos de ubicación de `reportes`, `tecnicos` y `publicaciones` deben tener índice `2dsphere` para consultas de cercanía.

```python
await db.reportes.create_index([("ubicacion", "2dsphere")])
```

## 8. Endpoints previstos

> Plantilla inicial. Los nombres pueden ajustarse durante el desarrollo.

**Autenticación y usuarios**

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/api/v1/auth/registro` | Crea cuenta (ciudadano o técnico). |
| POST | `/api/v1/auth/login` | Devuelve el token JWT. |
| GET | `/api/v1/usuarios/me` | Perfil del usuario autenticado. |

**Modo Cotidiano**

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET / POST | `/api/v1/publicaciones` | Listar y crear publicaciones de SegundaVida. |
| GET | `/api/v1/tecnicos` | Buscar técnicos por especialidad, zona, disponibilidad y valoración. |
| POST | `/api/v1/tecnicos/{id}/calificaciones` | Calificar un técnico. |
| POST | `/api/v1/bienestar/participaciones` | Enviar participación anónima. |

**Modo Emergencia**

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/api/v1/emergencia/activar` | Activa el Modo Emergencia (solo administrador). |
| POST | `/api/v1/emergencia/desactivar` | Desactiva el modo y vuelve al uso diario. |
| POST | `/api/v1/reportes` | Crea un reporte con ubicación, gravedad y evidencia. |
| GET | `/api/v1/reportes/{id}` | Consulta el estado de un caso. |
| PATCH | `/api/v1/reportes/{id}/estado` | Cambia el estado del reporte. |
| POST | `/api/v1/reportes/{id}/asignaciones` | Asigna recursos, técnicos o voluntarios. |
| GET | `/api/v1/auditoria` | Consulta el registro de cambios (administrador). |

## 9. Reglas de negocio clave

- **Estados de un reporte:** Reportado → En revisión → Asignado → En atención → Resuelto (RF-24). Cada cambio queda en auditoría (RF-05).
- **Identificador único** de seguimiento por reporte (RF-22).
- **Validación** de reportes por un coordinador para evitar falsas alarmas.
- **Reglas éticas del modelo de negocio:**
  1. En Modo Emergencia no se cobran comisiones.
  2. Los planes de visibilidad nunca influyen en qué técnicos se movilizan; se asigna solo por especialidad, ubicación y disponibilidad.
  3. Los datos de Mente Resiliente nunca se usan con fines comerciales.
- Los técnicos deben pasar por **verificación** antes de aparecer como verificados.

## 10. Seguridad y protección de datos

- Contraseñas con hash (por ejemplo `bcrypt`), nunca en texto plano.
- Autenticación con JWT y control de acceso por rol (RBAC) (RNF-04, RNF-05).
- Cifrado en tránsito (HTTPS) en producción.
- **Minimización y anonimización** de datos sensibles, en especial en Mente Resiliente: no guardar identificadores del usuario junto al texto analizado (RNF-06).
- CORS limitado a los orígenes del frontend.
- Validación estricta de entradas con Pydantic.

## 11. Trabajo sin conexión (apoyo al frontend)

Para que el modo offline del frontend funcione, el backend debe:

- Aceptar **identificadores de reporte generados en el cliente**, para evitar duplicados al reenviar.
- Responder de forma **idempotente**: reenviar el mismo reporte no crea uno nuevo.
- Aceptar una **fecha de creación del cliente** además de la de recepción.
- Permitir envío por partes: primero los datos del reporte y después las evidencias pesadas.

> Propuesta de implementación a validar con el equipo.

## 12. Pruebas

```bash
pytest
```

Prioridad de pruebas: autenticación y roles, activación del modo, ciclo de vida de un reporte, consultas geoespaciales y que ningún dato sensible se filtre a roles no autorizados.

## 13. Convenciones de trabajo

- Metodología **Scrum**, con entregas incrementales y roles de frontend, backend y base de datos.
- Ramas: `main` (estable), `develop` (integración) y `feature/<nombre>` por tarea.
- Commits en español, cortos y claros. Ejemplo: `feat: endpoint para crear reportes`.
- Todo cambio entra por *pull request* con al menos una revisión.

## 14. Decisiones pendientes

- Si la asignación de reportes será **automática por ubicación** o requerirá **aprobación del coordinador**.
- Modelo de NLP para Mente Resiliente y dónde se ejecutará.
- Proveedor de SMS para alertas.

## 15. Equipo

Sofía Jaramillo · Sara Salas · Juan Camilo Mosquera · Daniel García · Andrés Jiménez · Michael Zuluaga

Docente: Geraldine Toro · CIAF · Pereira, 2026
