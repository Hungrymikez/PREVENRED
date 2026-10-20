# Reglas transversales PrevenRed (extraído del doc 05)

## 1.6 Condiciones generales para todos los casos

Para no repetirlas en cada ficha, estas condiciones aplican a todos los casos de uso salvo que la ficha indique lo contrario:

- G1. Salvo CU-01 y CU-02, el actor tiene sesión vigente y su rol tiene permiso para la función en el modo operacional vigente (RF-03).

- G2. Las operaciones requieren conectividad, excepto las funciones de campo con soporte sin conexión (CU-37, RNF-08).

- G3. Los errores se muestran con mensajes claros y accionables, sin exponer datos técnicos ni personales (RNF-09).

- G4. Ante la falla de un servicio externo (GPS/mapas, Push/SMS, WhatsApp, NLP o almacenamiento) se aplican tiempos de espera, reintentos y degradación controlada, con monitoreo (RNF-13).

- G5. Los datos personales se tratan con finalidad, minimización, seguridad, acceso restringido y conservación limitada (RN-05, RN-06).

- G6. Las entradas se validan en el servidor y las API públicas aplican limitación de frecuencia (RNF-14).

- G7. Las decisiones técnicas de habitabilidad, evacuación o atención clínica las toma personal autorizado; el sistema solo las registra y las organiza.

## 4.2 Reglas de negocio

| **RN** | **Regla** | **Casos de uso que la aplican** |
| --- | --- | --- |
| **RN-01** | Solo un usuario autorizado activa o desactiva el Modo Emergencia | CU-04 |
| **RN-02** | Todo cambio de modo conserva trazabilidad | CU-04, CU-05, CU-09 |
| **RN-03** | NLP solo para análisis agregado | CU-23, CU-25, CU-26, CU-28 |
| **RN-04** | Habitabilidad solo por procedimiento técnico y rol autorizado | CU-10, CU-29, CU-35, CU-36, CU-39 |
| **RN-05** | Tratamiento de datos personales (finalidad, minimización, seguridad) | CU-01, CU-08, CU-11, CU-17, CU-22, CU-23, CU-24, CU-33, CU-34, CU-40, CU-46, CU-48 |
| **RN-06** | Archivos con control de acceso y retención | CU-11, CU-16, CU-17, CU-20, CU-34, CU-47 |
| **RN-07** | Mínimo privilegio y MFA en administración | CU-02, CU-03, CU-04, CU-08, CU-18 |

## 4.3 Requerimientos no funcionales

Algunos requerimientos no funcionales son transversales y aplican a todas las fichas (condiciones generales 1.6). En la tabla se listan los casos donde la ficha los referencia de forma explícita.

| **RNF** | **Categoría** | **Casos de uso** |
| --- | --- | --- |
| **RNF-01** | Rendimiento y escalabilidad | CU-06, CU-29, CU-30, CU-31 |
| **RNF-02** | Tiempo de respuesta | CU-45 |
| **RNF-03** | Rendimiento geoespacial | CU-12, CU-19, CU-40, CU-48 |
| **RNF-04** | Privacidad NLP | CU-23, CU-25, CU-26 |
| **RNF-05** | Cifrado | CU-37, CU-47 |
| **RNF-06** | Autenticación y autorización | CU-01, CU-02, CU-03, CU-04, CU-08 |
| **RNF-07** | Alta disponibilidad | CU-04, CU-06 |
| **RNF-08** | Offline-first | CU-29, CU-30, CU-31, CU-34, CU-36, CU-37 |
| **RNF-09** | Accesibilidad y legibilidad | Transversal: todas las interfaces (G3) |
| **RNF-10** | Navegación de crisis | CU-29, CU-30, CU-31 |
| **RNF-11** | Portabilidad móvil | Transversal: aplicaciones de ciudadanos, técnicos e inspectores |
| **RNF-12** | Recuperación ante desastres | Transversal: servicios críticos de la plataforma |
| **RNF-13** | Observabilidad | Transversal: servicios críticos (G4). Explícito en: CU-05, CU-37 |
| **RNF-14** | Protección contra abuso | CU-01, CU-02, CU-06, CU-47 |
| **RNF-15** | Mantenibilidad | Transversal: toda la plataforma |

# 5. Observaciones y puntos por confirmar

Al especificar los casos de uso se contrastaron los documentos 02, 03 y 04. Esto es lo que conviene confirmar o ajustar. Mientras se resuelve cada punto, la ficha afectada indica el supuesto con el que fue redactada.

| **#** | **Observación** | **Casos afectados** | **Propuesta** |
| --- | --- | --- | --- |
| **O-01** | Técnico / Voluntario en SegundaVida, Mente Resiliente y ofertas de ayuda. El documento 04 (M06, M08 y M12) los lista como usuarios; el documento 03 solo asocia esos casos al Ciudadano. | CU-11 a CU-15, CU-23, CU-33 | Confirmar. Las fichas usan Ciudadano como actor primario. Si aplica, asociar los casos al Técnico / Voluntario o dibujar una generalización hacia Ciudadano. |
| **O-02** | Operación sin conexión de reportes. RNF-08 y M05 cubren reportes de daño, de vías y solicitudes de ayuda, pero en el documento 03 CU-37 solo extiende CU-34 y CU-36. | CU-29, CU-30, CU-31, CU-37 | Agregar «extend» de CU-37 hacia CU-29, CU-30 y CU-31. Las fichas ya incluyen el flujo alternativo. |
| **O-03** | Auditoría de verificación, asignaciones y donaciones. RF-05 y M04 incluyen verificación de técnicos, asignaciones de recursos y donaciones, pero CU-05 solo se incluye desde CU-04, CU-08, CU-36, CU-42 y CU-43. | CU-18, CU-39, CU-41 (y como candidatos CU-10 y CU-46) | Agregar «include» de CU-05 en CU-18, CU-39 y CU-41, y decidir si los cambios de catálogo oficial y las exportaciones también se auditan. |
| **O-04** | Archivos adjuntos sin relación en el diagrama. Los documentos de verificación y el portafolio del técnico, y las evidencias fotográficas de la inspección (M10), usan almacenamiento de archivos, pero no incluyen CU-47. | CU-17, CU-36, CU-47 | Agregar «include» de CU-47 en CU-17 y CU-36. |
| **O-05** | Ubicación en necesidades, ofertas y voluntarios. El matching y la movilización dependen de la ubicación (RF-27, RF-28), pero CU-31, CU-33 y CU-44 no se relacionan con CU-48. | CU-31, CU-33, CU-44, CU-48 | Agregar «include» de CU-48 o definir que la ubicación se toma del perfil. |
| **O-06** | Detección de expresión de crisis. No está definido quién la detecta (la captura en CU-23, el análisis en CU-25 o la solicitud en CU-27), con qué criterio, ni qué datos se comparten con la autoridad. | CU-23, CU-25, CU-27, CU-28 | Definir con la autoridad competente y con quien construya el NLP. Mientras tanto, CU-28 solo muestra opciones de ayuda. |
| **O-07** | Anonimato frente a cuenta autenticada. El documento 04 habla de registro anónimo, pero el usuario inicia sesión. | CU-23, CU-25 | Definir si la respuesta se desvincula de la cuenta (anónima) o solo se oculta en el análisis (seudonimización). La ficha asume que la identidad no se expone en el análisis ni en el dashboard. |
| **O-08** | Frecuencia del registro de bienestar. El registro es semanal, pero no se define qué ocurre ante varios envíos en la misma semana. | CU-23 | Definir en el diseño: un envío por semana, o varios y se toma el último. |
| **O-09** | Consentimiento del propietario al convertir inventarios de SegundaVida en ofertas de ayuda (RF-26). No se define si hace falta su autorización. | CU-41 | Definir la regla de conversión (por ejemplo, solo publicaciones cuyo propietario lo autorizó) con la autoridad y el equipo. |
| **O-10** | Asignación de reportes. La entrevista deja pendiente si será automática o aprobada por un coordinador; el SRS no dice quién asigna. | CU-39 | CU-39 se modeló con el Administrador asignando. Confirmar con DIGER. |
| **O-11** | Ciclo de vida de incidentes. No se define si se permiten saltos o retrocesos entre los cinco estados, ni qué se considera caso crítico para la doble revisión. | CU-35, CU-36, CU-39 | Definir las transiciones válidas y el criterio de caso crítico con DIGER. |
| **O-12** | Video en cotización. RF-12 permite video de hasta 30 s con prioridad Media; falta confirmar si entra en la v1.0 (Anexo B, punto 5 del documento 04). | CU-20, CU-47 | Decidir si la v1.0 incluye video o solo fotografías. |
| **O-13** | Obligatoriedad de la foto en reportes de emergencia. RF-23 pide fotografía, pero exigirla puede frenar un reporte urgente. | CU-29, CU-30 | Definir con DIGER si se permite enviar un reporte sin foto. |
| **O-14** | «Estoy a salvo». Aparece en el prototipo y en M09, pero no tiene RF ni caso de uso. No se especificó aquí. | M09 | Registrar RF-31 mediante control de cambios (documento 04, §7.3) y agregar un caso nuevo (CU-49). |
| **O-15** | Funciones sin caso de uso propio. Recuperación de acceso y cierre de sesión, gestión de perfil y preferencias de notificación, gestión de publicaciones propias, reporte de publicaciones o usuarios y la vista simplificada «Cerca de ti» del ciudadano. | CU-02, CU-11, CU-16, CU-40 | Se documentaron como flujos alternativos. Decidir si se elevan a casos de uso propios. |
| **O-16** | Parámetros sin definir en los documentos base: duración y renovación de la sesión, mecanismo del segundo factor, umbral mínimo de población, intervalo de actualización del dashboard, límites de tamaño y cantidad de archivos, política de reintentos de notificaciones, regla de resolución de conflictos de sincronización, criterio de cercanía para duplicados y tiempos de retención. | CU-02, CU-03, CU-06, CU-26, CU-30, CU-37, CU-45, CU-47 | Definirlos en el documento 07 y con las entidades competentes. Las fichas los remiten al diseño. |
