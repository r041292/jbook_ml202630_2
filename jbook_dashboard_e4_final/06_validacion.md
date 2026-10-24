---
title: Validación estadística
description: Protocolo común, supuestos, siete pruebas de hipótesis con ajuste de Holm y BH, intervalos BCa, tamaños del efecto, MCS con los originales incluidos y superioridad estadísticamente verificada.
---

(sec-validacion)=
# Validación estadística

La condición R3 —**superioridad estadísticamente verificada**— exige que el modelo original tenga menor error que la mejor combinación benchmark y que cada uno de los 7 modelos base, que al menos tres pruebas distintas rechacen la igualdad con p ajustado por comparaciones múltiples, y que el efecto no sea despreciable (§6.1 de la guía). Este capítulo aplica ese protocolo a los tres originales con las pruebas de `analisis/pruebas_r3.py`, que comparan **cada original contra cada modelo base**, en especial contra el mejor benchmark, **XGBoost**.

Esta sección también incorpora una comparación directa con el **SVM lineal**, el modelo de referencia del proyecto, que es la comparación publicada en el dashboard. Ninguna prueba reentrena modelos ni vuelve a predecir: todas usan las predicciones OOF guardadas, que reproducen exactamente las métricas por fold registradas (prueba `test_pares_usan_los_mismos_folds_y_reproducen_metricas`).

(sec-protocolo-comun)=
## Protocolo común

- **Pareado estricto.** Los diez modelos (3 originales + 7 base) se evalúan sobre los **mismos cinco folds externos** `GroupKFold` por estudiante, con la misma semilla global 42 y el mismo preprocesamiento por familia ({ref}`sec-groupkfold`).
- **Unidades de análisis.** Las pruebas por fold usan las 5 métricas por fold; las pruebas por estudiante usan las pérdidas OOF de **1.309 registros de 1.293 estudiantes**, sumadas por estudiante (16 tienen dos registros, siempre en el mismo periodo).
- **Universos.** El **U10** (7 base + 3 originales) es el universo de R3. El **U15** es el del dashboard (9 modelos de la pestaña Originales, SVM y 5 clásicos, sin Decision Tree); se reproduce desde la comparación publicada en el dashboard. El **U16** añade Decision Tree al U15 como cálculo complementario, posible sin reentrenar porque sus OOF existen.
- **Test temporal.** Las 188 observaciones de 202530 solo se usan como complemento descriptivo; ninguna prueba de R3 depende de ellas.
- **Partición.** Los diez modelos comparten **una sola partición** de cinco folds externos; las pruebas por fold tienen, por tanto, cinco observaciones, mientras que las pruebas por estudiante usan las 1.293 unidades de la validación.

(sec-supuestos)=
## Supuestos y adecuación de cada prueba

Los datos son de **corte transversal**: cada estudiante aporta una o dos observaciones de un mismo periodo, y los folds no son tiempo. Por eso las pruebas pensadas para series de pronósticos —Giacomini–White, Clark–West, Reality Check/SPA y bootstrap estacionario {cite:p}`giacomini2006,clark2007,hansen2005,politis1994`— **no se aplican**: no hay una secuencia ordenada con horizonte, ni pares anidados restringido/ampliado, ni estacionariedad que justificar. Se usan las pruebas de la columna de corte transversal del Cuadro 3 de la guía y dos procedimientos globales:

1. **Wilcoxon de rangos con signo** {cite:p}`wilcoxon1945` sobre las diferencias de RMSE por fold (exacta). Supone diferencias simétricas e independientes; la independencia no se cumple porque los entrenamientos se solapan. **Con cinco folds el menor p bilateral posible es $2/2^5=0{,}0625$**: esta prueba no puede rechazar a α = 0,05 en este diseño.
2. **Permutación pareada por estudiante.** Bajo H0 las etiquetas de los dos modelos son intercambiables dentro de cada estudiante, lo que equivale a cambiar el signo de $D_i$ (diferencia de error cuadrático sumada por estudiante). No supone normalidad. Se usan 9.999 permutaciones; el menor p alcanzable es 10⁻⁴.
3. **t corregida de Nadeau–Bengio** {cite:p}`nadeau2003`, que incorpora la variabilidad del reentrenamiento entre folds:

$$
t=\frac{\bar d}{\sqrt{\left(\frac1k+\frac{n_{\text{val}}}{n_{\text{fit}}}\right)s_d^2}},\qquad k=5,\ \frac{n_{\text{val}}}{n_{\text{fit}}}=0{,}25,\ \text{gl}=k-1=4 .
$$ (eq-nb)

4. **Bootstrap pareado BCa** {cite:p}`efron1987` de ΔRMSE remuestreando estudiantes completos (9.999 réplicas, semilla 42), con aceleración por *jackknife* de estudiantes. El p bilateral se obtiene **invirtiendo el intervalo**: es el menor α para el que el IC BCa al nivel 1 − α excluye el cero.
5. **Contraste tipo Diebold–Mariano por estudiante con corrección HLN** {cite:p}`diebold1995,harvey1997`, el mismo del dashboard. El DM se diseñó para series de tiempo; aquí la observación es el estudiante, el error estándar es robusto por estudiante en lugar de HAC y la corrección HLN se aplica con $h=1$:

$$
\bar d=\frac{\sum_i D_i}{\sum_i n_i},\quad
\widehat{SE}=\frac{1}{\sum_i n_i}\sqrt{\frac{G}{G-1}\sum_{i=1}^{G}\big(D_i-\bar d\,n_i\big)^2},\quad
t_{\text{HLN}}=\frac{\bar d}{\widehat{SE}}\sqrt{\frac{G-1}{G}}\sim t_{G-1}.
$$ (eq-dm)

6. **Friedman → Nemenyi** {cite:p}`friedman1937,demsar2006`: Friedman sobre los rangos del RMSE en cada fold y la diferencia crítica $CD=q_\alpha\sqrt{k(k+1)/(6N)}$. Con $N=5$ bloques está por debajo de los diez que recomienda SciPy para la aproximación χ².
7. **Model Confidence Set** {cite:p}`hansen2011` con el estadístico $T_R=\max_{i,j}\lvert t_{ij}\rvert$ y eliminación secuencial; el bootstrap **enumera los 3.125 remuestreos** posibles de cinco folds (sin error Monte Carlo). Se conservan los modelos con p MCS ≥ 0,10.

Las pruebas 2, 4 y 5 tratan los modelos como **fijos** y miden la incertidumbre por la muestra de estudiantes; las pruebas 1 y 3 incorporan la variabilidad de **reentrenar** con otros datos, pero solo tienen cinco observaciones. Las tres pruebas por estudiante contrastan casi la misma hipótesis sobre la misma muestra, de modo que su coincidencia **no es evidencia independiente**.

**Ajuste por comparaciones múltiples.** Cada prueba por pares tiene una familia de **21 comparaciones** (3 originales × 7 base), ajustada con Holm {cite:p}`holm1979` como criterio principal y con Benjamini–Hochberg {cite:p}`benjamini1995` como complemento. Como contraste más exigente se ajustan también las **105 comparaciones** por pares juntas. En total se realizaron 105 comparaciones por pares, dos pruebas de Friedman (U10 y U16), 21 pares de Nemenyi en U10 y dos procedimientos MCS. **Tamaños del efecto** sobre el MSE por fold: δ de Cliff {cite:p}`cliff1993` con los umbrales de {cite:t}`romano2006` y $d_z$ de Cohen emparejado.

(sec-tabla-resumen)=
## Tabla resumen

La {numref}`tab-resumen-modelos` reúne lo que pide §6.3: media ± DE del bucle externo, IC 95 % bootstrap del RMSE OOF por estudiantes y tiempos de entrenamiento e inferencia.

```{include} analisis/tablas/resumen_modelos.md
```

**Condición 1 de R3.** Los tres originales tienen menor RMSE medio externo que el mejor benchmark (XGBoost, 0,8156) y que cada uno de los 7 modelos base. La ventaja es pequeña: 0,015 puntos para el KRR centrado, 0,013 para el GPR–XGBoost y 0,010 para el TN-KRR, y los intervalos del RMSE OOF de originales y benchmarks se solapan ampliamente. El tiempo del GPR–XGBoost no incluye la etapa GPR compartida entre candidatos ({ref}`sec-gprxgb-complejidad`).

(sec-pruebas-xgboost)=
## Pruebas frente al mejor benchmark y al SVM lineal

Las tablas siguientes tienen las columnas de §6.3 —prueba, hipótesis nula, supuestos, estadístico, p crudo, p ajustado, tamaño del efecto y conclusión— para cada original frente a XGBoost. La conclusión usa el p de Holm de la familia de 21.

```{include} analisis/tablas/pruebas_m5.md
```

```{include} analisis/tablas/pruebas_m15.md
```

```{include} analisis/tablas/pruebas_m19.md
```

**KRR centrado y GPR–XGBoost** mejoran a XGBoost en las dos pruebas no paramétricas por estudiante (permutación, p Holm = 0,031; BCa, p Holm = 0,022) y entran al MCS mientras XGBoost queda fuera. El contraste DM-HLN queda justo en el límite (p Holm = 0,052) aunque su p crudo es 0,009–0,011. Ni Wilcoxon (que no puede rechazar con cinco folds) ni la t corregida (p crudo 0,11 y 0,14) ni Nemenyi (Δ rango 2,2 frente a una CD de 6,06) detectan diferencia. **TN-KRR** no se distingue de XGBoost en ninguna prueba por pares (p crudo 0,15–0,45); solo entra al MCS con XGBoost fuera.

(sec-tnkrr-svm)=
### TN-KRR frente al SVM lineal

La comparación que plantea el TN-KRR es frente al SVM lineal, el modelo de referencia del proyecto ({numref}`tab-pruebas-m19-svm`).

```{include} analisis/tablas/pruebas_m19_svm.md
```

El TN-KRR tiene menor RMSE que el SVM en **los cinco folds externos** (0,8056 frente a 0,8241 de media) y lo supera en cuatro pruebas: permutación por estudiante (p Holm = 0,0030), bootstrap BCa (ΔRMSE = −0,0187; IC 95 % [−0,0295; −0,0095]; p Holm = 0,0008), contraste DM-HLN (p Holm = 0,0041) y MCS (el SVM queda fuera con p = 0,022). Las tres pruebas por pares siguen siendo significativas con el ajuste de Holm sobre las 105 comparaciones (p = 0,021; 0,005 y 0,022). El efecto es pequeño según Cliff (δ = −0,20) y grande en su versión emparejada ($d_z$ = −1,03), porque la mejora se repite en todos los folds. Wilcoxon (p = 0,0625, el mínimo posible con cinco folds) y la t corregida (p = 0,19) no alcanzan significancia.

(sec-pruebas-todas)=
## Pruebas frente a los siete modelos base

La {numref}`tab-matriz-holm` resume las 105 comparaciones. En todas las celdas significativas la diferencia favorece al original; ningún original resulta significativamente **peor** que un benchmark.

```{include} analisis/tablas/matriz_holm.md
```

```{figure} images/e4/ic_bca_pares.png
:alt: Tres paneles con la diferencia de RMSE de cada original frente a cada modelo base e intervalos BCa al 95 %.
:name: fig-ic-bca

Δ RMSE OOF (original − base, en puntos de nota) con IC 95 % BCa por estudiante. Naranja: p Holm < 0,05 en la familia de 21; a la izquierda de la línea discontinua el original tiene menor error.
```

La [](#fig-ic-bca) muestra el patrón con claridad. Frente a los modelos lineales, KNN, Random Forest y Decision Tree, los tres originales mejoran de forma significativa en las pruebas por estudiante. Frente a XGBoost, los intervalos de KRR centrado y GPR–XGBoost quedan enteramente por debajo de cero pero cerca de él (−0,025 a −0,003), y el de TN-KRR cruza el cero. La t corregida solo rechaza frente a Decision Tree, el modelo claramente inferior.

```{include} analisis/tablas/efectos_r3.md
```

Los tamaños del efecto de la {numref}`tab-efectos-r3` no son despreciables frente a XGBoost: δ = −0,28 (KRR centrado), −0,36 (GPR–XGBoost) y −0,20 (TN-KRR), con $d_z$ de −1,40, −1,27 y −0,53. El $d_z$ es grande porque las diferencias tienen el mismo signo en casi todos los folds; δ es pequeño o mediano porque las distribuciones de MSE por fold se solapan. En la escala de la nota la diferencia absoluta es de 0,010–0,015 puntos de RMSE.

(sec-friedman-mcs)=
## Procedimientos globales: Friedman, Nemenyi y MCS

```{figure} images/e4/cd_u10.png
:alt: Diagrama de diferencia crítica de Nemenyi con los rangos promedio de los diez modelos; los tres originales en naranja.
:name: fig-cd-u10

Diagrama de diferencia crítica (Nemenyi, α = 0,05) del universo U10: rango promedio del RMSE en los cinco folds (1 = menor error). La barra superior es la CD.
```

Friedman rechaza la igualdad de rangos en U10 (χ² = 29,07; gl = 9; p = 0,0006). En la [](#fig-cd-u10), KRR centrado y GPR–XGBoost comparten el mejor rango promedio (2,6), seguidos de TN-KRR (3,2) y XGBoost (4,8). Con cinco bloques la diferencia crítica es 6,06: de los 21 pares original–base, solo los tres pares con Decision Tree (rango 10) la superan; frente a KNN (8,4) la diferencia de KRR centrado y GPR–XGBoost es 5,8. Nemenyi no distingue a los originales de XGBoost ni de los lineales; es una falta de potencia, no evidencia de equivalencia.

```{include} analisis/tablas/mcs_u10.md
```

El MCS de U10 ({numref}`tab-mcs-u10`) conserva **exactamente los tres originales** (p MCS = 1, 0,446 y 0,341) y elimina a todos los benchmarks: XGBoost sale con p = 0,0003 y los lineales con p entre 0,009 y 0,022. El MCS es el procedimiento global con control del *data snooping* que pide el Cuadro 3. Su limitación es que el remuestreo de cinco folds dependientes no garantiza la cobertura nominal del 90 %, y un p MCS no es la probabilidad de que un modelo sea el mejor.

El cálculo complementario U16 ({numref}`tab-mcs-u16`), que incluye modelos candidatos adicionales del dashboard (véase la nota de la sección [](#sec-migrado)), confirma que añadir Decision Tree al universo del dashboard no cambia el conjunto: siguen KRR centrado, GPR–XGBoost, TN-KRR y SVR RBF (Friedman χ² = 51,22; gl = 15; p < 0,0001).

```{include} analisis/tablas/mcs_u16.md
```

(sec-migrado)=
## Comparación estadística publicada en el dashboard

:::{note} Modelos adicionales del dashboard
En el dashboard se evaluaron más modelos candidatos, además de los tres originales que se decidió presentar en este informe (KRR centrado, TN-KRR y GPR–XGBoost): SVR RBF, DenseWeight-XGBoost, TCR-XGBoost, LinXGBoost, logicDT y RIM. Por eso aparecen en las tablas siguientes. La lista completa, con la explicación y el artículo de referencia de cada modelo, puede consultarse en el dashboard o en la sección [Explicación de cada modelo](https://r041292.github.io/jbook_ml202630_2/modelos-originales/#explicaci-n-de-cada-modelo) del informe anterior.
:::

Las tablas de esta sección se regeneran desde los CSV de la comparación del dashboard (`analisis/salidas/heredadas/originales/`, con hash en `source_manifest.json`) y documentan la comparación que publica el dashboard sobre el universo U15.

```{include} analisis/tablas/her_mcs15.md
```

El MCS del dashboard ({numref}`tab-her-mcs15`) conserva los tres originales y SVR RBF; **el SVM lineal queda fuera (p MCS = 0,0346)**, igual que XGBoost, Ridge, Lasso, Random Forest y KNN. Friedman sobre los 15 modelos da χ² = 43,47 (gl 14; p = 7,2 × 10⁻⁵) y Nemenyi (CD = 9,59) solo separa al GPR–XGBoost y al KRR centrado de RIM y KNN. Entre los cuatro finalistas ningún par difiere ({numref}`tab-her-finalistas`).

```{include} analisis/tablas/her_finalistas.md
```

(sec-dm-svm)=
### Contraste tipo Diebold–Mariano por estudiante frente al SVM

```{include} analisis/tablas/her_dm_cv.md
```

Frente al SVM lineal, los tres originales mejoran en la validación cruzada por estudiante ({numref}`tab-her-dm-cv`): KRR centrado ΔRMSE = −0,0234 (p HLN = 0,0016), GPR–XGBoost −0,0215 (0,0096) y TN-KRR −0,0187 (0,0003), con intervalos bootstrap enteramente negativos. **Con el ajuste de Holm para las 3 comparaciones** pedidas en el plan, los p HLN ajustados son 0,0033, 0,0096 y 0,0009: las tres mejoras se mantienen. La versión `Precalculo/resultados/e3/contraste_estudiante/` (Holm 3: 0,0057, 0,0119 y 0,0020) llega a la misma conclusión; según su código usa como referencia las OOF del SVM histórico (`resultados/e3/train.csv.gz`), por eso sus cifras difieren ligeramente. La t corregida, en cambio, **no confirma** ninguna de las tres mejoras (p = 0,19–0,33): la evidencia frente al SVM es sólida en la muestra de estudiantes, pero no frente a la variabilidad de reentrenar.

```{include} analisis/tablas/her_dm_test.md
```

En el test 202530 los signos se conservan (ΔRMSE de −0,020 a −0,027 frente al SVM), pero ninguna diferencia de los tres originales es significativa ({numref}`tab-her-dm-test`). Frente a XGBoost la ventaja en el test es aún menor ({numref}`tab-test-complemento`): −0,005 para los dos kernels y −0,011 para el híbrido, sin significancia.

```{include} analisis/tablas/test_complemento.md
```

(sec-veredicto-r3)=
## Superioridad estadísticamente verificada

```{include} analisis/tablas/veredicto.md
```

La {numref}`tab-veredicto` aplica la definición operativa de §6.1 —menor error medio, al menos tres pruebas con p ajustado favorables y efecto no despreciable— frente al mejor benchmark y frente al SVM lineal. Los tres originales tienen además menor RMSE medio que cada uno de los siete modelos base.

- **Frente al SVM lineal, los tres originales son superiores** con el ajuste de Holm por prueba y con Benjamini–Hochberg. El **TN-KRR y el KRR centrado lo son también con Holm sobre las 105 comparaciones**, el criterio más exigente.
- **Frente a XGBoost, el KRR centrado y el GPR–XGBoost son superiores** con Holm por prueba (permutación, bootstrap BCa y MCS) y con Benjamini–Hochberg; con Holm sobre las 105 comparaciones solo el MCS los separa.
- **El TN-KRR no se distingue de XGBoost**: frente a ese benchmark solo el MCS lo separa.

**Discusión.** El resultado depende del criterio de multiplicidad, de la referencia y del tipo de prueba, y se lee con cuatro consideraciones. (1) Las pruebas que rechazan son las que tratan los modelos como fijos y usan 1.293 estudiantes; las que incorporan la variabilidad de reentrenar (Wilcoxon, t corregida, Nemenyi) no rechazan, y con cinco folds Wilcoxon no puede hacerlo. (2) Las tres pruebas por estudiante no son evidencia independiente entre sí. (3) La ventaja es de 0,010–0,015 puntos de RMSE frente a XGBoost y de 0,019–0,023 frente al SVM, menor que la desviación estándar entre folds (0,034–0,048); en el test temporal conserva el signo pero no alcanza significancia. (4) Los originales se eligieron entre varias alternativas de la pestaña Originales evaluadas en la misma validación, una selección que ninguna corrección cubre. Las causas probables de la falta de potencia son el tamaño de la muestra (1.309 registros), el ruido irreducible de la nota (el caso de mayor error es el mismo para todas las familias) y una sola partición de cinco folds. La conclusión es que **los modelos de kernel y el híbrido mejoran de forma consistente al SVM lineal y, con menor margen, a XGBoost en esta muestra de estudiantes**; las pruebas que incorporan la variabilidad del reentrenamiento y el test temporal no alcanzan significancia con cinco folds y 188 estudiantes.
