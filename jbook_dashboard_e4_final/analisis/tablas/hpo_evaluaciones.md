:::{table} Configuraciones evaluadas / ajustes de pipeline en la búsqueda final de cada modelo base (cada configuración a fidelidad completa cuesta 5 ajustes).
:label: tab-hpo-evaluaciones

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 27 / 135 | 16 / 80 | 20 / 100 | 11 / 55 | 28 / 140 |
| SVM lineal | 48 / 240 | 16 / 80 | 20 / 100 | 16 / 80 | 28 / 140 |
| Ridge | 8 / 40 | 16 / 80 | 20 / 100 | 12 / 60 | 28 / 140 |
| Lasso | 9 / 45 | 16 / 80 | 20 / 100 | 12 / 60 | 28 / 140 |
| Random Forest | 27 / 135 | 16 / 80 | 20 / 100 | 13 / 65 | 28 / 140 |
| KNN | 32 / 160 | 15 / 75 | 20 / 100 | 9 / 45 | 27 / 135 |
| Decision Tree | 72 / 360 | 16 / 80 | 20 / 100 | 11 / 55 | 28 / 140 |
:::
