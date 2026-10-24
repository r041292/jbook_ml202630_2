:::{table} Diferencia de RMSE medio externo y tamaños de efecto (MSE por fold) de cada original frente a cada base.
:label: tab-efectos-r3

| Original | Base | Δ RMSE medio CV | Folds ganados | δ de Cliff | Magnitud | d_z de Cohen |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| KRR centrado | SVM lineal | −0,0231 | 4 de 5 | −0,20 | pequeña | −0,89 |
| KRR centrado | KNN | −0,0541 | 5 de 5 | −0,68 | grande | −3,26 |
| KRR centrado | Ridge | −0,0243 | 4 de 5 | −0,20 | pequeña | −0,91 |
| KRR centrado | Lasso | −0,0279 | 4 de 5 | −0,20 | pequeña | −0,96 |
| KRR centrado | Random Forest | −0,0288 | 5 de 5 | −0,60 | grande | −2,14 |
| KRR centrado | XGBoost | −0,0146 | 4 de 5 | −0,28 | pequeña | −1,40 |
| KRR centrado | Decision Tree | −0,0939 | 5 de 5 | −1,00 | grande | −8,41 |
| TN-KRR | SVM lineal | −0,0186 | 5 de 5 | −0,20 | pequeña | −1,03 |
| TN-KRR | KNN | −0,0495 | 5 de 5 | −0,68 | grande | −2,43 |
| TN-KRR | Ridge | −0,0197 | 4 de 5 | −0,12 | despreciable | −1,08 |
| TN-KRR | Lasso | −0,0233 | 4 de 5 | −0,20 | pequeña | −1,14 |
| TN-KRR | Random Forest | −0,0242 | 4 de 5 | −0,28 | pequeña | −1,15 |
| TN-KRR | XGBoost | −0,0100 | 4 de 5 | −0,20 | pequeña | −0,53 |
| TN-KRR | Decision Tree | −0,0893 | 5 de 5 | −0,92 | grande | −5,51 |
| GPR–XGBoost | SVM lineal | −0,0213 | 4 de 5 | −0,20 | pequeña | −0,73 |
| GPR–XGBoost | KNN | −0,0523 | 5 de 5 | −0,68 | grande | −2,94 |
| GPR–XGBoost | Ridge | −0,0225 | 4 de 5 | −0,20 | pequeña | −0,74 |
| GPR–XGBoost | Lasso | −0,0260 | 4 de 5 | −0,28 | pequeña | −0,81 |
| GPR–XGBoost | Random Forest | −0,0269 | 5 de 5 | −0,60 | grande | −1,97 |
| GPR–XGBoost | XGBoost | −0,0128 | 4 de 5 | −0,36 | mediana | −1,27 |
| GPR–XGBoost | Decision Tree | −0,0920 | 5 de 5 | −1,00 | grande | −7,32 |
:::
