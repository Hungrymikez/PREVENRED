# Índice de casos de uso (doc 05)


Los 48 casos de uso se distribuyen así: 22 de prioridad Crítica, 21 Alta y 5 Media. La prioridad de cada caso hereda la de su módulo en el documento 04; los casos de reputación, cotización con evidencia, moderación y contacto por WhatsApp son de prioridad Media según la matriz del SRS.

| **Código** | **Caso de uso** | **Módulo** | **Actor primario** | **Prioridad** | **Requisitos** |
| --- | --- | --- | --- | --- | --- |
| **CU-01** | Registrarse | M01 | Ciudadano; Técnico / Voluntario | Crítica | RF-03, RNF-06, RNF-14, RN-05 |
| **CU-02** | Iniciar sesión | M01 | Todos los roles | Crítica | RF-03, RF-02, RNF-06, RNF-14, RN-07 |
| **CU-03** | Validar autenticación reforzada (MFA) | M01 | Administrador | Crítica | RF-01, RNF-06, RN-07 |
| **CU-04** | Cambiar modo operacional | M02 | Administrador | Crítica | RF-01, RF-02, RF-03, RF-04, RN-01, RN-02, RN-07, RNF-06, RNF-07 |
| **CU-05** | Registrar auditoría | M04 | Sistema | Crítica | RF-05, RN-02, RNF-13 |
| **CU-06** | Emitir notificaciones de crisis | M03 | Sistema | Crítica | RF-04, RF-24, RNF-01, RNF-07, RNF-14 |
| **CU-07** | Recibir notificaciones de crisis | M03 | Ciudadano; Técnico / Voluntario; Inspector | Crítica | RF-04, RF-24 |
| **CU-08** | Gestionar usuarios y roles | M01 | Administrador | Crítica | RF-03, RN-05, RN-07, RNF-06 |
| **CU-09** | Consultar registros de auditoría | M04 | Administrador | Crítica | RF-05, RN-02 |
| **CU-10** | Configurar catálogos y capas de mapa | M10 / M11 | Administrador | Crítica | RF-20, RF-25, RN-04 |
| **CU-11** | Publicar material | M06 | Ciudadano | Alta | RF-06, RN-05, RN-06 |
| **CU-12** | Buscar materiales por ubicación | M06 | Ciudadano | Alta | RF-07, RNF-03 |
| **CU-13** | Solicitar alquiler de herramienta | M06 | Ciudadano | Alta | RF-08 |
| **CU-14** | Gestionar reservas de mis herramientas | M06 | Ciudadano | Alta | RF-08 |
| **CU-15** | Calificar y reseñar | M06 / M07 | Ciudadano | Media | RF-09 |
| **CU-16** | Moderar contenido y reseñas | M06 / M07 | Administrador | Media | RF-09, RF-12, RN-06 |
| **CU-17** | Gestionar perfil de técnico | M07 | Técnico / Voluntario | Alta | RF-10, RN-05, RN-06 |
| **CU-18** | Verificar técnico | M01 / M07 | Administrador | Alta | RF-10, RF-05, RN-07 |
| **CU-19** | Buscar servicios técnicos | M07 | Ciudadano | Alta | RF-11, RNF-03 |
| **CU-20** | Solicitar cotización con evidencia | M07 | Ciudadano | Media | RF-12, RN-06 |
| **CU-21** | Responder cotización | M07 | Técnico / Voluntario | Media | RF-12 |
| **CU-22** | Contactar técnico por WhatsApp | M07 | Ciudadano | Media | RF-13, RN-05 |
| **CU-23** | Responder encuesta de bienestar | M08 | Ciudadano | Alta | RF-14, RF-16, RN-03, RN-05, RNF-04 |
| **CU-24** | Otorgar consentimiento y aceptar aviso de privacidad | M08 / M01 | Ciudadano | Alta | RF-14, RN-05 |
| **CU-25** | Procesar análisis NLP | M08 | Servicio NLP/IA | Alta | RF-15, RF-16, RN-03, RNF-04 |
| **CU-26** | Consultar indicadores psicosociales | M08 | Administrador | Alta | RF-17, RN-03, RNF-04 |
| **CU-27** | Solicitar apoyo profesional | M08 | Ciudadano | Alta | RF-18 |
| **CU-28** | Activar flujo de atención de crisis | M08 | Sistema | Alta | RF-18, RN-03 |
| **CU-29** | Reportar daño en vivienda | M09 | Ciudadano | Crítica | RF-22, RNF-01, RNF-08, RNF-10, RN-04 |
| **CU-30** | Reportar vía bloqueada o escombros | M09 | Ciudadano | Crítica | RF-23, RF-22, RNF-01, RNF-08, RNF-10 |
| **CU-31** | Solicitar ayuda | M09 | Ciudadano | Crítica | RF-27, RNF-01, RNF-08, RNF-10 |
| **CU-32** | Consultar estado de mis casos | M09 | Ciudadano | Crítica | RF-22, RF-24 |
| **CU-33** | Ofrecer ayuda o donación | M12 | Ciudadano | Alta | RF-27, RF-26, RN-05 |
| **CU-34** | Registrar censo de inmueble | M10 | Inspector | Crítica | RF-19, RF-22, RNF-08, RN-05, RN-06 |
| **CU-35** | Clasificar nivel de daño | M10 | Inspector | Crítica | RF-20, RF-21, RN-04 |
| **CU-36** | Ejecutar flujo de habitabilidad | M10 | Inspector | Crítica | RF-21, RF-20, RF-05, RNF-08, RN-04 |
| **CU-37** | Sincronizar información sin conexión | M05 | Sistema | Crítica | RNF-08, RNF-05, RNF-13 |
| **CU-38** | Consultar asignaciones | M13 / M10 | Inspector; Técnico / Voluntario | Alta | RF-28, RF-24 |
| **CU-39** | Gestionar incidentes | M09 | Administrador | Crítica | RF-24, RF-22, RF-05, RN-04 |
| **CU-40** | Consultar mapa multicapa | M11 | Administrador; Inspector | Crítica | RF-25, RNF-03, RN-05 |
| **CU-41** | Gestionar banco de ayudas | M12 | Administrador | Alta | RF-26, RF-27, RF-05 |
| **CU-42** | Ejecutar matching de donaciones | M12 | Administrador | Alta | RF-27, RF-05 |
| **CU-43** | Gestionar bolsa de voluntariado | M13 | Administrador | Alta | RF-28, RF-10, RF-05 |
| **CU-44** | Postularse como voluntario | M13 | Técnico / Voluntario | Alta | RF-28, RF-10 |
| **CU-45** | Consultar dashboard municipal | M14 | Administrador | Alta | RF-29, RF-17, RF-24, RF-25, RNF-02 |
| **CU-46** | Exportar reportes oficiales | M14 | Administrador | Alta | RF-30, RN-05 |
| **CU-47** | Adjuntar archivos multimedia | M09 / M10 | Sistema | Crítica | RF-06, RF-12, RF-19, RF-23, RNF-05, RNF-14, RN-06 |
| **CU-48** | Obtener ubicación | M11 | Sistema | Crítica | RF-07, RF-19, RF-23, RNF-03, RN-05 |
