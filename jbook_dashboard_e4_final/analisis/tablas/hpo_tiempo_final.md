:::{table} Tiempo de pared (s) de la búsqueda final en todo train, por modelo base y estrategia.
:label: tab-hpo-tiempo-final

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 127,33 | 76,97 | 97,48 | 37,15 | 97,43 |
| SVM lineal | 15,47 | 2,77 | 3,22 | 2,79 | 3,70 |
| Ridge | 6,72 | 1,08 | 1,40 | 0,84 | 1,85 |
| Lasso | 6,18 | 1,26 | 1,96 | 1,16 | 2,01 |
| Random Forest | 34,86 | 21,77 | 24,19 | 16,08 | 24,57 |
| KNN | 8,19 | 1,35 | 1,75 | 1,21 | 2,97 |
| Decision Tree | 14,48 | 1,61 | 2,05 | 1,13 | 2,50 |
:::
