:::{table} Cálculo complementario: MCS de los 15 modelos del dashboard más Decision Tree (16), α = 0,10.
:label: tab-mcs-u16

| Modelo | Rango promedio de pérdida | MSE medio CV | p MCS | En MCS | Paso de eliminación |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPR–XGBoost (OOF agrupado) | 3,0 | 0,6459 | 0,4464 | Sí | 15 |
| Kernel Ridge RBF | 3,2 | 0,6429 | 1,0000 | Sí | 16 |
| Truncated Newton KRR RBF | 4,2 | 0,6506 | 0,3488 | Sí | 14 |
| SVR RBF | 4,4 | 0,6534 | 0,3488 | Sí | 13 |
| DenseWeight-XGBoost | 6,4 | 0,6644 | 0,0010 | No | 6 |
| XGBoost | 6,8 | 0,6661 | 0,0010 | No | 8 |
| TCR-XGBoost | 6,8 | 0,6663 | 0,0010 | No | 7 |
| SVM lineal | 7,8 | 0,6810 | 0,0346 | No | 12 |
| Ridge | 8,0 | 0,6832 | 0,0336 | No | 11 |
| Lasso | 8,8 | 0,6895 | 0,0192 | No | 10 |
| Random Forest | 10,4 | 0,6891 | < 0,0001 | No | 4 |
| LinXGBoost (hojas completas E3) | 11,6 | 0,7177 | < 0,0001 | No | 5 |
| logicDT propio (adaptado) | 11,8 | 0,7171 | 0,0045 | No | 9 |
| KNN | 13,4 | 0,7324 | < 0,0001 | No | 3 |
| RIM (port E3) | 13,6 | 0,7481 | < 0,0001 | No | 2 |
| Decision Tree | 15,8 | 0,8016 | < 0,0001 | No | 1 |
:::
