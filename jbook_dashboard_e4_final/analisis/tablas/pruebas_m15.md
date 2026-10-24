:::{table} GPR–XGBoost frente al mejor benchmark (XGBoost): pruebas de hipótesis con las columnas de §6.3.
:label: tab-pruebas-m15

| Prueba | H0 | Supuestos verificados | Estadístico | p crudo | p ajustado (Holm, 21) | p Holm global (105) | Tamaño del efecto (MSE por fold) | Conclusión |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Wilcoxon por fold | Mediana de las diferencias de RMSE por fold = 0 | Diferencias simétricas; pares por fold. No se cumple la independencia (entrenamientos solapados); p mínimo bilateral con n = 5: 0,0625 | W (suma de rangos) = 1,00 | 0,1250 | 1,0000 | 1,0000 | δ = −0,36 (mediana); d_z = −1,27 | No se rechaza H0 |
| Permutación pareada por estudiante | Las etiquetas de modelo son intercambiables dentro de cada estudiante (Δ MSE = 0) | Estudiantes independientes (1.293; 16 con dos filas agrupadas); no requiere normalidad | Δ MSE medio = −0,0202 | 0,0106 | 0,0312 | 0,4770 | δ = −0,36 (mediana); d_z = −1,27 | Original mejor |
| t corregida de Nadeau–Bengio | Δ RMSE esperado = 0 al reentrenar con otros datos | Normalidad aproximada de 5 diferencias; corrige el solapamiento con n_val/n_fit = 0,25 | t (gl = 4) = −1,81 · IC [−0,0324; 0,0068] | 0,1448 | 1,0000 | 1,0000 | δ = −0,36 (mediana); d_z = −1,27 | No se rechaza H0 |
| Bootstrap pareado BCa | Δ RMSE = 0 (el IC 95 % BCa contiene el 0) | Estudiantes intercambiables; corrige sesgo y asimetría (BCa); modelos fijos | Δ RMSE = −0,0125 · IC [−0,0219; −0,0030] | 0,0102 | 0,0221 | 0,4673 | δ = −0,36 (mediana); d_z = −1,27 | Original mejor |
| Diebold–Mariano por estudiante (HLN) | Δ MSE medio = 0 | Adaptación de corte transversal: SE robusto por estudiante y corrección HLN (h = 1); modelos fijos | z·√((G−1)/G), t con G−1 gl = −2,55 · IC [−0,0220; −0,0028] | 0,0109 | 0,0519 | 0,4781 | δ = −0,36 (mediana); d_z = −1,27 | No se rechaza H0 |
| Friedman → Nemenyi (U10) | Rangos promedio iguales | Bloques = 5 folds (menos de los 10 recomendados); CD controla la familia | χ² = 29,07 (gl 9); Δ rango = −2,2; CD = 6,06 | 0,0006 | CD (familiar) | — | δ = −0,36 (mediana); d_z = −1,27 | No supera la CD |
| Model Confidence Set (U10) | Igual capacidad predictiva del conjunto | Bootstrap exacto de 5 folds (3.125 remuestreos); folds dependientes | p MCS original = 0,4464; XGBoost = 0,0003 | — | α = 0,10 (procedimiento) | — | δ = −0,36 (mediana); d_z = −1,27 | Original en el MCS y XGBoost fuera |
:::
