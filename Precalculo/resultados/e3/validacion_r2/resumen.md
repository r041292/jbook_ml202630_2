# Validación completa con R² — E3

18 modelos actuales en el mismo test temporal202530:188 estudiantes. Mayor R²
es mejor. Delta=modelo−SVM: positivo indica mejora. Permutación bilateral directa
de la diferencia R² por estudiante99999 y bootstrap pareado10000; semilla42.
IC95% marginales de R² y su diferencia en modelos_r2.csv. Holm17 corresponde
a17 contrastes frente a SVM. Holm21 incorpora4 pares adicionales frente a XGBoost.

| Método | R² test | Δ R² vs. SVM | p bilateral | p Holm17 |
|---|---:|---:|---:|---:|
| TabICLv2 | 0.464774 | +0.036232 | 0.02624 | 0.41984 |
| TabPFN 2.5 original | 0.464223 | +0.035680 | 0.06888 | 0.99090 |
| TabPFN 2.5 fine-tuned | 0.460527 | +0.031984 | 0.08018 | 1.00000 |
| Kernel Ridge RBF | 0.456316 | +0.027774 | 0.09620 | 1.00000 |
| CatBoost | 0.455368 | +0.026826 | 0.21864 | 1.00000 |
| XGBoost | 0.454641 | +0.026099 | 0.21102 | 1.00000 |
| TCR-XGBoost | 0.452929 | +0.024387 | 0.24432 | 1.00000 |
| Ridge | 0.441545 | +0.013003 | 0.31128 | 1.00000 |
| Lasso | 0.438424 | +0.009881 | 0.15770 | 1.00000 |
| KNN | 0.433995 | +0.005452 | 0.82690 | 1.00000 |
| HRT-Boost | 0.433442 | +0.004900 | 0.78618 | 1.00000 |
| logicDT propio (adaptado) | 0.430104 | +0.001561 | 0.94434 | 1.00000 |
| SVM lineal | 0.428543 | +0.000000 | — | — |
| Random Forest | 0.413751 | -0.014791 | 0.51846 | 1.00000 |
| RIM (port E3) | 0.378834 | -0.049709 | 0.16266 | 1.00000 |
| XBART (GFR) | 0.378447 | -0.050096 | 0.12166 | 1.00000 |
| coPILOT | 0.374472 | -0.054071 | 0.06606 | 0.99090 |
| Dummy media | -0.047571 | -0.476113 | 0.00002 | 0.00034 |

## Resultado e interpretación

TabICLv2 tiene el mayor R² test:0.4647742613 frente a SVM0.4285425650;
diferencia+0.0362316963. Nominal p0.02624; Holm17=.41984; Holm21=.47232.
Ningún modelo mejora significativamente a SVM después de Holm. Dummy es
significativamente peor. R² puede ser negativo; no es el cuadrado de la
correlación entre nota y predicción.

Los p-valores y el ranking coinciden con RMSE por una razón matemática:
RMSE=sqrt(SSE/n) y R²=1−SSE/SST. Al comparar sobre las mismas observaciones,
n y SST son comunes. La diferencia R² es (SSE_referencia−SSE_modelo)/SST.
El intercambio pareado por estudiante produce el mismo contraste bilateral;
no son dos evidencias independientes. Se verificó la igualdad de los21
p-valores con los existentes y las mismas correcciones de Holm.

## Validación cruzada y alcance

validacion_cruzada_r2.csv contiene media y SD(ddof0) de los5 folds externos,
R² OOF reunido y R² temporal. folds_r2.csv detalla85 evaluaciones externas
de17 modelos. Media de R² por fold y R² de todas las OOF son cantidades
diferentes; no deben confundirse con el resultado temporal.

TabPFN ajustado tiene R² test, pero no una nueva CV OOF independiente: los
pesos finales ya se ajustaron con todo train. Sus campos de CV quedan vacíos.
No se reconstruye una CV ficticia con esos pesos.

Esta evaluación usa los modelos/grillas ya seleccionados por RMSE. No se
reoptimizaron hiperparámetros por R². En un mismo fold, maximizar R² equivale
a minimizar RMSE; promediar métricas entre folds sí puede cambiar la selección,
porque cambian las varianzas de y y la ponderación implícita de cada fold.

El test reutilizado mantiene carácter exploratorio; IC/p condicionales a
los modelos, sin variabilidad de reentrenamiento. No rechazar H0 no prueba
equivalencia. Datos, variables, grupos, modelos y sus resultados previos intactos.

[Definición oficial de R²](https://scikit-learn.org/stable/modules/model_evaluation.html#r2-score).
