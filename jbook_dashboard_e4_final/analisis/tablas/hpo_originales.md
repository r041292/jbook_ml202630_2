:::{table} Búsqueda final de los tres originales por estrategia: RMSE interno (en negrita, la elegida), configuraciones evaluadas y tiempos de pared. En el GPR–XGBoost los tiempos excluyen la etapa GPR, calculada una vez por conjunto de ajuste.
:label: tab-hpo-originales

| Modelo | Medida | Grid | Random | TPE | DEAP | Halving |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| KRR centrado | RMSE interno | 0,800408 | 0,811287 | **0,798165** | 0,800460 | 0,811287 |
|  | Evaluaciones | 35 | 16 | 20 | 16 | 28 |
|  | Búsqueda final (s) | 8,55 | 2,75 | 3,48 | 2,89 | 2,53 |
|  | 5 externas (s) | 34,71 | 15,65 | 19,65 | 15,89 | 18,68 |
| TN-KRR | RMSE interno | 0,803685 | 0,816305 | **0,801160** | 0,802747 | 0,816305 |
|  | Evaluaciones | 35 | 16 | 20 | 16 | 28 |
|  | Búsqueda final (s) | 5,36 | 2,26 | 2,93 | 2,19 | 2,31 |
|  | 5 externas (s) | 25,49 | 10,69 | 15,56 | 11,99 | 14,30 |
| GPR–XGBoost | RMSE interno | 0,804104 | 0,815841 | 0,803197 | **0,802333** | 0,815841 |
|  | Evaluaciones | 54 | 16 | 20 | 23 | 28 |
|  | Búsqueda final (s) | 215,71 | 97,77 | 91,87 | 115,02 | 244,38 |
|  | 5 externas (s) | 2.512,14 | 417,37 | 389,75 | 468,98 | 827,42 |
:::
