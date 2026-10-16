# Dashboard de Precálculo

Proyecto académico de Machine Learning de la Universidad del Norte. Explora los datos del nivelatorio de Precálculo en ALEK y compara modelos de regresión para predecir la nota del primer parcial. La rama `e3` contiene el estado actual de los experimentos; los enlaces históricos conservan las entregas anteriores.

**Autores:** Rubiel Velásquez y Valentina Figueroa.

## Enlaces

- [Dashboard publicado en Render](https://precalculo-dashboard.onrender.com/).
- [Jupyter Book del proyecto: desarrollo e interpretación del dashboard](https://r041292.github.io/jbook_ml202630_2/).
- [Jupyter Book del entregable 1: datos, EDA y modelo base](https://r041292.github.io/jbook_ml202630_1/).

**Tecnologías:** Python, Dash, Plotly, scikit-learn y Jupyter Book.

## Avances del entregable 3

La rama `e3` reúne el dashboard con datos reales, validación por estudiante y
test temporal y 26 modelos evaluados: 22 históricos, tres variantes de
XGBoost y LinXGBoost con hojas lineales. Sus comparaciones estadísticas
documentan por separado la familia histórica Holm55, Holm12 para las variantes
XGBoost y Holm7 para LinXGBoost. La entrega anterior se conserva en `main`.

- [Guía de E3, notebooks y reproducción local](Precalculo/README_E3.md).
- [Panorama vigente de los 26 modelos](Precalculo/resultados/e3/resumen_completo/resumen.md) y [CSV general](Precalculo/resultados/e3/resumen_completo/modelos.csv).
- [Validación R² de los 26 modelos, CV y 125 resultados por fold](Precalculo/resultados/e3/validacion_r2/resumen.md).
- [Resultados SVR RBF y RaFFLE](Precalculo/resultados/e3/svr_rbf_raffle/resumen.md).
- [Variantes de XGBoost: etapa histórica de 25 modelos](Precalculo/resultados/e3/xgboost_variantes/resumen.md).
- [LinXGBoost y ranking RMSE de 26 modelos](Precalculo/resultados/e3/linxgboost/resumen.md).

SVR RBF conserva el mejor resultado puntual: RMSE 0.892225 y R² 0.471418.
TabICLv2 y TabPFN 2.5 original siguen segundo y tercero. LinXGBoost queda
cuarto (RMSE 0.899069), frente a XGBoost octavo (0.906274), pero su ventaja
no es significativa tras Holm7 y su error OOF es mayor. Las variantes
XGBoost ampliado, DenseWeight y DART no mejoran el RMSE test del original.
El uso reiterado del test hace exploratoria la comparación. El ranking no
demuestra superioridad estadística entre los primeros puestos; los ajustes
Holm55, Holm12 y Holm7 corresponden a familias distintas.
