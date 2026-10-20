# Índice de colecciones MongoDB (doc 09 + ajustes)

Marcas: `+` campo agregado · `~` campo cambiado · sin marca = como el doc 09. Ajustes explicados en `docs/09_rectificacion_bd_mongodb.md`.

| Colección | Contexto | Casos de uso |
|---|---|---|
| `users` | identity | CU-01 CU-02 CU-03 CU-08 CU-06 |
| `roles` | identity | CU-08 (RF-03) |
| `operational_modes` | operating_mode | CU-04 |
| `audit_logs` | audit | CU-05 CU-09 |
| `materials` | marketplace | CU-11 CU-12 CU-16 |
| `tools` | marketplace | CU-11 CU-13 CU-14 |
| `reservations` | marketplace | CU-13 CU-14 |
| `transactions` | marketplace | CU-13 CU-15 |
| `reviews` | marketplace | CU-15 CU-16 |
| `technicians` | services | CU-17 CU-18 CU-19 CU-44 |
| `service_requests` | services | CU-19 CU-20 |
| `quotes` | services | CU-20 CU-21 |
| `wellbeing_surveys` | wellbeing | CU-23 |
| `nlp_analysis` | wellbeing | CU-25 |
| `support_requests` | wellbeing | CU-27 CU-28 |
| `properties` | fieldwork | CU-34 |
| `property_inspections` | fieldwork | CU-35 CU-36 CU-37 |
| `incidents` | incidents | CU-29 CU-30 CU-32 CU-39 |
| `incident_status_history` | incidents | CU-39 (RF-24) |
| `map_layers` | geo | CU-10 CU-40 |
| `catalogs` | geo | CU-10 (RF-20) |
| `donations` | aid | CU-33 CU-42 |
| `aid_needs` | aid | CU-31 CU-32 CU-42 |
| `donation_matches` | aid | CU-42 |
| `aid_inventory` | aid | CU-41 |
| `volunteers` | volunteering | CU-43 CU-44 |
| `assignments` | volunteering | CU-38 CU-43 |
| `notifications` | notifications | CU-06 CU-07 |
| `files` | media | CU-47 |
| `counters` | shared | RF-22 |
| `sessions` | identity | CU-02 A4 |
| `password_resets` | identity | CU-02 A2 |
| `wellbeing_consents` | wellbeing | CU-24 |
| `wellbeing_indicators` | wellbeing | CU-26 CU-45 |
