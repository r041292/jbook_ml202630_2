# Dashboard de Precálculo

- Implementar el dashboard en esta carpeta con Dash y Plotly.
- Usar exclusivamente `../Precalculo/venv/`; no crear otro entorno virtual.
- Leer `CONTEXT.md` y `../Precalculo/CONTEXT.md` antes de modificar el dashboard.
- **Actualizar `Dash/CONTEXT.md` en cada modificación del dashboard**, incluyendo decisiones, fuentes, resultados de validación y limitaciones vigentes.
- No sobrescribir notebooks ni CSV fuente. Mantener test separado desde el inicio.
- EDA sobre train válido; conservar outliers válidos. Excluir inconsistencias según las reglas de negocio de Precalculo.
- Nunca usar `nota_final` como predictor ni en matrices de correlación.
- Todo el flujo activo (EDA, modelos y dashboard) usa exclusivamente la alternativa 1: perturbación local, CSV de `../Precalculo/comparacion_aumentacion/`. Los CSV anteriores son históricos y no se usan como fuente activa.
- Las métricas, intervalos, diagnósticos y curva de aprendizaje se leen de `../Precalculo/resultados/`, exportados al reejecutar los notebooks; no mantener cifras antiguas escritas a mano.
- Los filtros evalúan subgrupos del modelo global; no reentrenar por programa/asignatura ni ajustar usando test.
- Si cambian las fuentes de modelado, regenerar `data/` con `prepare_data.py` y validar correspondencia con el notebook.
