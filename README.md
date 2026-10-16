# Dashboard de Precálculo

Proyecto académico de Machine Learning de la Universidad del Norte. Explora los datos del nivelatorio de Precálculo en ALEK y evalúa un modelo lineal para predecir la nota del primer parcial. Incluye un dashboard interactivo y un informe con metodología, resultados e interpretaciones, basado en la primera entrega del proyecto.

**Autores:** Rubiel Velásquez y Valentina Figueroa.

## Enlaces

- [Dashboard publicado en Render](https://precalculo-dashboard.onrender.com/).
- [Jupyter Book del proyecto: desarrollo e interpretación del dashboard](https://r041292.github.io/jbook_ml202630_2/).
- [Jupyter Book del entregable 1: datos, EDA y modelo base](https://r041292.github.io/jbook_ml202630_1/).

**Tecnologías:** Python, Dash, Plotly, scikit-learn y Jupyter Book.

## Avances del entregable 3

La rama `e3` reúne el dashboard con datos reales, validación por estudiante y
test temporal, más 22 modelos principales, tres variantes metodológicas de
XGBoost y LinXGBoost con hojas lineales. Sus comparaciones estadísticas
documentan por separado la familia histórica Holm55, Holm12 para las variantes
XGBoost y Holm7 para LinXGBoost. La entrega anterior se conserva en `main`.

- [Guía de E3, notebooks y reproducción local](Precalculo/README_E3.md).
- [Panorama completo de modelos](Precalculo/resultados/e3/resumen_completo/resumen.md).
- [Validación completa con R²](Precalculo/resultados/e3/validacion_r2/resumen.md).
- [Resultados SVR RBF y RaFFLE](Precalculo/resultados/e3/svr_rbf_raffle/resumen.md).
- [Variantes de XGBoost y ranking integrado de 25 modelos](Precalculo/resultados/e3/xgboost_variantes/resumen.md).
- [LinXGBoost y ranking RMSE de 26 modelos](Precalculo/resultados/e3/linxgboost/resumen.md).
