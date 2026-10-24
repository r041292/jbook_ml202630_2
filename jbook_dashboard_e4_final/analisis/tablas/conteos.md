:::{table} Conteos por etapa del ETL (`resultados/e3/particion.json`).
:label: tab-conteos

| Etapa | Registros | Estudiantes | Observación |
| --- | ---: | ---: | --- |
| Fuente `Datos_Brutos.csv` (6 periodos, 31 columnas) | 1.527 | 1.506 | 2023–2025 |
| Sin nota del primer parcial | 30 | — | Excluidas del aprendizaje supervisado |
| Con objetivo | 1.497 | — | Base de la partición |
| Purga de estudiantes del periodo reservado | 0 | 0 | Ningún estudiante en ambos lados |
| Incumplimientos de reglas de negocio (train / test) | 0 / 0 | — | Ninguna fila excluida |
| Train válido (202310–202510) | 1.309 | 1.293 | EDA, búsqueda y validación anidada |
| Test temporal (202530) | 188 | 188 | Solo evaluación final |
| Atípicos eliminados | 0 | — | Se conservan los valores extremos válidos |
:::
