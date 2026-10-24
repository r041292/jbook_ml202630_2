:::{table} Tiempos de pared (s) de la ejecución activa de los modelos base, desde `tiempos/20261018_102325_af643f83/eventos.jsonl`.
:label: tab-tiempos-base

| Modelo | Búsqueda final (5 estrategias) | Búsquedas externas (5 folds) | Refit final | Inferencia OOF (5 lotes) | Inferencia test (188 filas) |
| --- | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 436,36 | 1.754,56 | 1,326 | 0,141 | 0,0346 |
| SVM lineal | 27,94 | 129,80 | 0,088 | 0,079 | 0,0155 |
| Ridge | 11,89 | 73,83 | 0,067 | 0,082 | 0,0157 |
| Lasso | 12,56 | 59,90 | 0,112 | 0,074 | 0,0152 |
| Random Forest | 121,47 | 605,60 | 1,317 | 0,181 | 0,0803 |
| KNN | 15,47 | 94,81 | 0,063 | 0,135 | 0,0221 |
| Decision Tree | 21,76 | 87,59 | 0,079 | 0,071 | 0,0134 |
:::
