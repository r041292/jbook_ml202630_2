:::{table} Superioridad estadísticamente verificada de cada original según la definición operativa de §6.1, frente al mejor benchmark (XGBoost) y frente al SVM lineal.
:label: tab-veredicto

| Original | Frente a | Menor RMSE medio | Pruebas favorables (p Holm por prueba) | Efecto (MSE por fold) | Superior · Holm por prueba | Superior · BH global | Superior · Holm global |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KRR centrado | XGBoost | Sí (0,8010 vs 0,8156) | 3: Permutación pareada por estudiante; Bootstrap pareado BCa; MCS (U10) | δ = −0,28; d_z = −1,40 | **Sí** | Sí | No |
| TN-KRR | XGBoost | Sí (0,8056 vs 0,8156) | 1: MCS (U10) | δ = −0,20; d_z = −0,53 | **No** | No | No |
| GPR–XGBoost | XGBoost | Sí (0,8028 vs 0,8156) | 3: Permutación pareada por estudiante; Bootstrap pareado BCa; MCS (U10) | δ = −0,36; d_z = −1,27 | **Sí** | Sí | No |
| KRR centrado | SVM lineal | Sí (0,8010 vs 0,8241) | 4: Permutación pareada por estudiante; Bootstrap pareado BCa; Diebold–Mariano por estudiante (HLN); MCS (U10) | δ = −0,20; d_z = −0,89 | **Sí** | Sí | Sí |
| TN-KRR | SVM lineal | Sí (0,8056 vs 0,8241) | 4: Permutación pareada por estudiante; Bootstrap pareado BCa; Diebold–Mariano por estudiante (HLN); MCS (U10) | δ = −0,20; d_z = −1,03 | **Sí** | Sí | Sí |
| GPR–XGBoost | SVM lineal | Sí (0,8028 vs 0,8241) | 3: Permutación pareada por estudiante; Bootstrap pareado BCa; MCS (U10) | δ = −0,20; d_z = −0,73 | **Sí** | Sí | No |
:::
