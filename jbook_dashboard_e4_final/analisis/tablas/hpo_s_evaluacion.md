:::{table} Segundos por evaluación (búsqueda final ÷ configuraciones; cada evaluación ajusta 5 pipelines en paralelo) y tiempo medio de un ajuste interno individual.
:label: tab-hpo-s-evaluacion

| Modelo | Grid | Random | TPE | DEAP | Halving | Ajuste interno medio (TPE, s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 4,716 | 4,810 | 4,874 | 3,378 | 3,480 | 3,1282 |
| SVM lineal | 0,322 | 0,173 | 0,161 | 0,174 | 0,132 | 0,0621 |
| Ridge | 0,840 | 0,067 | 0,070 | 0,070 | 0,066 | 0,0216 |
| Lasso | 0,687 | 0,079 | 0,098 | 0,097 | 0,072 | 0,0351 |
| Random Forest | 1,291 | 1,361 | 1,209 | 1,237 | 0,877 | 0,6078 |
| KNN | 0,256 | 0,090 | 0,088 | 0,134 | 0,110 | 0,0219 |
| Decision Tree | 0,201 | 0,101 | 0,103 | 0,102 | 0,089 | 0,0308 |
:::
