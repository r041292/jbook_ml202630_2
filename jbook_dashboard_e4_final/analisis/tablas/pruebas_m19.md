:::{table} TN-KRR frente al mejor benchmark (XGBoost): pruebas de hipótesis con las columnas de §6.3.
:label: tab-pruebas-m19

| Prueba | H0 | Supuestos verificados | Estadístico | p crudo | p ajustado (Holm, 21) | p Holm global (105) | Tamaño del efecto (MSE por fold) | Conclusión |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Wilcoxon por fold | Mediana de las diferencias de RMSE por fold = 0 | Diferencias simétricas; pares por fold. No se cumple la independencia (entrenamientos solapados); p mínimo bilateral con n = 5: 0,0625 | W (suma de rangos) = 3,00 | 0,3125 | 1,0000 | 1,0000 | δ = −0,20 (pequeña); d_z = −0,53 | No se rechaza H0 |
| Permutación pareada por estudiante | Las etiquetas de modelo son intercambiables dentro de cada estudiante (Δ MSE = 0) | Estudiantes independientes (1.293; 16 con dos filas agrupadas); no requiere normalidad | Δ MSE medio = −0,0156 | 0,1469 | 0,1469 | 1,0000 | δ = −0,20 (pequeña); d_z = −0,53 | No se rechaza H0 |
| t corregida de Nadeau–Bengio | Δ RMSE esperado = 0 al reentrenar con otros datos | Normalidad aproximada de 5 diferencias; corrige el solapamiento con n_val/n_fit = 0,25 | t (gl = 4) = −0,8328 · IC [−0,0435; 0,0234] | 0,4518 | 1,0000 | 1,0000 | δ = −0,20 (pequeña); d_z = −0,53 | No se rechaza H0 |
| Bootstrap pareado BCa | Δ RMSE = 0 (el IC 95 % BCa contiene el 0) | Estudiantes intercambiables; corrige sesgo y asimetría (BCa); modelos fijos | Δ RMSE = −0,0096 · IC [−0,0215; 0,0046] | 0,1748 | 0,1748 | 1,0000 | δ = −0,20 (pequeña); d_z = −0,53 | No se rechaza H0 |
| Diebold–Mariano por estudiante (HLN) | Δ MSE medio = 0 | Adaptación de corte transversal: SE robusto por estudiante y corrección HLN (h = 1); modelos fijos | z·√((G−1)/G), t con G−1 gl = −1,43 · IC [−0,0226; 0,0040] | 0,1520 | 0,1520 | 1,0000 | δ = −0,20 (pequeña); d_z = −0,53 | No se rechaza H0 |
| Friedman → Nemenyi (U10) | Rangos promedio iguales | Bloques = 5 folds (menos de los 10 recomendados); CD controla la familia | χ² = 29,07 (gl 9); Δ rango = −1,6; CD = 6,06 | 0,0006 | CD (familiar) | — | δ = −0,20 (pequeña); d_z = −0,53 | No supera la CD |
| Model Confidence Set (U10) | Igual capacidad predictiva del conjunto | Bootstrap exacto de 5 folds (3.125 remuestreos); folds dependientes | p MCS original = 0,3408; XGBoost = 0,0003 | — | α = 0,10 (procedimiento) | — | δ = −0,20 (pequeña); d_z = −0,53 | Original en el MCS y XGBoost fuera |
:::
