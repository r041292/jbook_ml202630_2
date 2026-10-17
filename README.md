# Dashboard de Precálculo

Proyecto académico de Machine Learning de la Universidad del Norte. Explora los datos reales del nivelatorio de Precálculo en ALEK y compara 26 modelos y variantes para predecir la nota del primer parcial. El dashboard presenta CV externa por estudiante, contraste temporal, significancia frente al SVM y simulación con el pipeline original de Kernel Ridge RBF.

**Autores:** Rubiel Velásquez y Valentina Figueroa.

## Enlaces

La revisión E3 compara procedimientos principalmente mediante **CV externa**;
el test temporal es un contraste complementario y no selecciona familias.
**Kernel Ridge RBF** es el candidato elegido por CV entre los26 modelos activos
(RMSE medio0.801325), con pipeline original guardado y verificado. GPR sola fue
retirada del flujo activo; se mantiene el híbrido GPR–XGBoost como experimento
distinto. Ninguna mejora frente al SVM es significativa tras t corregida
aproximada y Holm24. Cinco folds sin repeticiones ofrecen evidencia exploratoria,
sin ganador estadístico confirmado. SVR RBF conserva el mínimo puntual del test.

Ver [README E3](Precalculo/README_E3.md) y
[significancia CV: método, resultados y límites](Precalculo/resultados/e3/cv_externa/README.md).

- [Dashboard publicado en Render](https://precalculo-dashboard.onrender.com/).
- [Jupyter Book del proyecto: desarrollo e interpretación del dashboard](https://r041292.github.io/jbook_ml202630_2/).
- [Jupyter Book del entregable 1: datos, EDA y modelo base](https://r041292.github.io/jbook_ml202630_1/).

**Tecnologías:** Python, Dash, Plotly, scikit-learn y Jupyter Book.
