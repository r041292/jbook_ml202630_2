:::{table} Model Confidence Set del universo de 10 modelos (7 base + 3 originales), α = 0,10.
:label: tab-mcs-u10

| Modelo | Rango promedio de pérdida | MSE medio CV | p MCS | En MCS | Paso de eliminación |
| --- | ---: | ---: | ---: | ---: | ---: |
| **KRR centrado** | 2,6 | 0,6429 | 1,0000 | Sí | 10 |
| **GPR–XGBoost** | 2,6 | 0,6459 | 0,4464 | Sí | 9 |
| **TN-KRR** | 3,2 | 0,6506 | 0,3408 | Sí | 8 |
| XGBoost | 4,8 | 0,6661 | 0,0003 | No | 4 |
| SVM lineal | 5,2 | 0,6810 | 0,0218 | No | 7 |
| Ridge | 5,4 | 0,6832 | 0,0189 | No | 6 |
| Lasso | 6,0 | 0,6895 | 0,0093 | No | 5 |
| Random Forest | 6,8 | 0,6891 | < 0,0001 | No | 3 |
| KNN | 8,4 | 0,7324 | < 0,0001 | No | 2 |
| Decision Tree | 10,0 | 0,8016 | < 0,0001 | No | 1 |
:::
