---
title: Modelo original
description: Formulación, pseudocódigo, complejidad, código, pruebas unitarias, ablación e interpretabilidad de los tres modelos originales — KRR centrado, TN-KRR y GPR–XGBoost.
---

(sec-modelo-original)=
# Modelo original

Por la retroalimentación del profesor, el proyecto presenta **tres modelos originales**. Cada uno ataca una limitación distinta de los benchmarks y tiene una parte propia diferente: el KRR centrado modifica qué aprende el kernel (la desviación respecto de la media); el TN-KRR programa el solver que resuelve el sistema dual; el GPR–XGBoost define una regla de combinación con meta-variables fuera del fold por estudiante. Este capítulo dedica una sección a cada uno, con los requisitos de §5.4 de la guía, y cierra con una comparación común.

Los tres pasan por **exactamente el mismo protocolo** que los benchmarks: los mismos cinco folds externos `GroupKFold` por estudiante, la misma semilla 42, cinco folds internos y las mismas cinco estrategias de búsqueda con los mismos presupuestos (Random 16, TPE 20, DEAP 8 × 4, Halving 16 → 8 → 4; el Grid conserva su grilla). La ejecución activa es `20261020_153034_consolidada` (`Precalculo/resultados/e3/originales_busquedas/`), construida con `Precalculo/busquedas_originales_e3.py:56-81`.

(sec-limitacion)=
## Limitación que se ataca

El {ref}`sec-datos` mostró una relación **no lineal** entre dominio, Saber 11 y nota, y una población heterogénea con cola de notas bajas. Los benchmarks lineales (SVM, Ridge, Lasso) no representan esa no linealidad y los árboles (Random Forest, XGBoost) la aproximan por escalones con unos 1.300 estudiantes. Los métodos de kernel ofrecen una función suave y regularizada; el proceso gaussiano añade una medida de incertidumbre por estudiante. Las tres propuestas exploran esa dirección.

(sec-krr)=
## Kernel Ridge RBF con objetivo centrado

(sec-krr-r2)=
### Originalidad (R2) verificada en el código

El modelo se construye en `Precalculo/modelos_scopus_e3.py:131-137`: un `KernelRidge` de scikit-learn con kernel RBF, **envuelto en un `TransformedTargetRegressor` con `StandardScaler(with_std=False)`**, sobre el preprocesamiento canónico de 67 columnas.

```{literalinclude} analisis/codigo/modelos_scopus_e3.py
:language: python
:lines: 131-137
:lineno-start: 131
:caption: Construcción del KRR centrado (`modelos_scopus_e3.make_model('kernel_ridge')`).
:label: cod-krr
```

La parte propia es la decisión de modelado —no penalizar el nivel medio de la nota— y su integración al protocolo anidado. **No existe una clase propia**: el modelo es una composición de tres componentes de librería. Frente al Cuadro 1 de la guía, que no acepta «cambiar la pérdida, el kernel o el criterio de partición mediante un parámetro de la librería», este es el caso más débil de los tres en R2; se presenta como original por la validación del profesor y se declara aquí la observación.

(sec-krr-formulacion)=
### Motivación y formulación

`KernelRidge` no tiene intercepto: aprende $f(x)=\sum_i c_i\,k(x_i,x)$ y la penalización empuja la función hacia **cero**. Como la nota media es cercana a 3,5, un KRR directo sesga las predicciones hacia 0 cuanto mayor es `alpha` o más lejos está un estudiante de los de entrenamiento. El centrado resuelve el problema regularizado sobre la desviación $y-\bar y$:

$$
\hat f=\arg\min_{f\in\mathcal H_k}\;\sum_{i=1}^{n}\big(y_i-\bar y-f(x_i)\big)^2+\alpha\lVert f\rVert^2_{\mathcal H_k},
\qquad k(x,x')=\exp\!\big(-\gamma\lVert x-x'\rVert^2\big).
$$ (eq-krr-objetivo)

**Derivación.** Por el teorema del representante, $f=\sum_j c_j k(x_j,\cdot)$, de modo que $f(X)=Kc$ y $\lVert f\rVert^2=c^\top Kc$. La [](#eq-krr-objetivo) se convierte en $J(c)=\lVert y_c-Kc\rVert^2+\alpha c^\top Kc$ con $y_c=y-\bar y\mathbf 1$. Su gradiente es $\nabla J=-2K(y_c-Kc)+2\alpha Kc=2K\big[(K+\alpha I)c-y_c\big]$; como $K$ es semidefinida positiva y $\alpha>0$, $K+\alpha I$ es definida positiva y la solución única es

$$
\hat c=(K+\alpha I)^{-1}(y-\bar y\mathbf 1),\qquad \hat y(x)=\bar y+\sum_{i=1}^{n}\hat c_i\,k(x_i,x).
$$ (eq-krr-solucion)

**Propiedad.** Si $x$ está lejos de todos los estudiantes de entrenamiento, $k(x_i,x)\to 0$ y la [](#eq-krr-solucion) da $\hat y(x)\to\bar y$ (≈ 3,4994 en el ajuste final), mientras que el KRR sin centrar tiende a 0. La prueba unitaria `test_krr_centrado_aprende_y_revierte_a_la_media` lo verifica numéricamente. Centrar $y$ no es idéntico a estimar un intercepto libre junto con $f$ (eso exigiría también centrar el kernel, como la *centered KRR* de {cite:t}`elkhalil2019`): equivale a fijar el desplazamiento en $\bar y$. La media se aprende solo con las notas de cada entrenamiento (interno, externo o final), sin filtrar validación ni test. El procedimiento tiene respaldo en {cite:t}`eckhard2014`, que no compara con y sin centrado.

(sec-krr-pseudocodigo)=
### Pseudocódigo

```{code-block} text
:caption: KRR centrado.
:label: alg-krr
Entradas: X ∈ R^{n×p} (67 columnas transformadas), y ∈ R^n, α > 0, γ > 0
Salidas:  ȳ, coeficientes duales ĉ ∈ R^n, función ŷ(·)
Entrenamiento:
  1. ȳ ← (1/n) Σ_i y_i                         # aprendido solo con el entrenamiento
  2. y_c ← y − ȳ·1
  3. K_ij ← exp(−γ‖x_i − x_j‖²) para i, j = 1..n
  4. Resolver (K + αI) ĉ = y_c                  # Cholesky / solución cerrada
Predicción para x*:
  5. k*_i ← exp(−γ‖x_i − x*‖²);  ŷ(x*) ← ȳ + k*ᵀ ĉ
Parada: solución cerrada (sin iteraciones).
```

(sec-krr-complejidad)=
### Complejidad y tiempos

Construir $K$ cuesta $O(n^2p)$, factorizar $K+\alpha I$ cuesta $O(n^3)$ y la memoria es $O(n^2)$; predecir $m$ casos cuesta $O(mnp)$. Con $n=1.309$ y $p=67$, $K$ tiene 1,7 millones de entradas. Empíricamente, el refit final tardó **0,078 s** y la inferencia del test (188 filas) **0,0096 s**; la búsqueda final con cinco estrategias, 20,2 s (registro `20261019_083039_147f9845`). Con $n=1.309$ el término cúbico es pequeño en términos absolutos: el refit completo, factorización incluida, tarda menos de una décima de segundo.

(sec-tnkrr)=
## Truncated Newton KRR (TN-KRR)

(sec-tnkrr-r2)=
### Originalidad (R2) verificada en el código

`Precalculo/tn_krr_e3.py:14` define `TruncatedNewtonKernelRidgeRegressor(RegressorMixin, BaseEstimator)`. Hereda de scikit-learn **solo** para ser compatible con `fit`/`predict`, `clone` y `Pipeline`; el kernel RBF (líneas 31-37), la validación de entradas (39-49), el bucle de gradiente conjugado con sus tres criterios de parada (57-109) y la predicción (118-124) están programados en NumPy. El algoritmo es el TR-KRR de {cite:t}`maalouf2014`, aplicado por {cite:t}`abdulla2022`; la contribución del proyecto es la implementación propia, su integración al pipeline E3 y la búsqueda anidada.

(sec-tnkrr-formulacion)=
### Motivación y formulación

Resolver $(K+\alpha I)a=y$ por factorización cuesta $O(n^3)$. El gradiente conjugado (CG) {cite:p}`hestenes1952` resuelve el mismo sistema minimizando la cuadrática

$$
\phi(a)=\tfrac12\,a^\top(K+\alpha I)\,a-y^\top a,\qquad \nabla\phi(a)=(K+\alpha I)a-y=-r ,
$$ (eq-tn-cuadratica)

cuyo único mínimo es la solución del sistema porque $A=K+\alpha I$ es simétrica definida positiva. Partiendo de $a_0=0$ ($r_0=d_0=y$), cada iteración avanza en una dirección $A$-conjugada:

$$
\eta_t=\frac{r_t^\top r_t}{d_t^\top A d_t},\quad a_{t+1}=a_t+\eta_t d_t,\quad r_{t+1}=r_t-\eta_t A d_t,\quad
d_{t+1}=r_{t+1}+\frac{r_{t+1}^\top r_{t+1}}{r_t^\top r_t}\,d_t .
$$ (eq-tn-cg)

**Terminación y error.** En aritmética exacta CG converge en a lo sumo $n$ pasos; además, con $\kappa=\operatorname{cond}(A)\le(\lambda_{\max}(K)+\alpha)/\alpha$,

$$
\lVert a_t-a^\ast\rVert_A\le 2\left(\frac{\sqrt\kappa-1}{\sqrt\kappa+1}\right)^{t}\lVert a_0-a^\ast\rVert_A .
$$ (eq-tn-cota)

La implementación se **trunca** con los controles del artículo: $\lVert r_t\rVert\le 0{,}5$, 200 iteraciones o 25 iteraciones sin mejora; el límite de iteraciones garantiza la terminación aunque la cota converja lentamente. Detenerse antes del óptimo actúa como regularización implícita (parada temprana) adicional a $\alpha$. A diferencia del KRR centrado, **el objetivo no se centra**: se usa $y$ tal como aparece en el sistema del artículo. La predicción es $\hat y(x)=\sum_i a_i\,k(x_i,x)$.

(sec-tnkrr-pseudocodigo)=
### Pseudocódigo

```{code-block} text
:caption: TN-KRR (gradiente conjugado truncado).
:label: alg-tnkrr
Entradas: X ∈ R^{n×p}, y ∈ R^n, α > 0, γ > 0, T_max = 200, τ = 0,5, S = 25
Salidas:  coeficientes a, iteraciones t, norma ‖r‖, motivo de parada
  1. Validar entradas (finitas, α > 0, γ > 0, límites positivos)
  2. A ← K(X, X; γ) + αI;  a ← 0;  r ← y;  d ← r;  mejor ← ‖r‖;  s ← 0
  3. para t = 1..T_max:
  4.     q ← A d;  η ← (rᵀr)/(dᵀq)   (si dᵀq ≤ 0: error de curvatura)
  5.     a ← a + η d;  r_nuevo ← r − η q
  6.     si ‖r_nuevo‖ ≤ τ: parar («residual_tolerance»)
  7.     si ‖r_nuevo‖ < mejor: mejor ← ‖r_nuevo‖; s ← 0  si no: s ← s + 1
  8.     si s ≥ S: parar («no_improvement»)
  9.     d ← r_nuevo + (r_nuevoᵀ r_nuevo / rᵀr) d;  r ← r_nuevo
 10. Predicción: ŷ(x*) ← K(x*, X; γ) a
Parada: tolerancia del residuo, T_max iteraciones o S iteraciones sin mejora.
```

```{literalinclude} analisis/codigo/tn_krr_e3.py
:language: python
:lines: 57-116
:lineno-start: 57
:caption: Bucle de gradiente conjugado truncado y criterios de parada (`Precalculo/tn_krr_e3.py`).
:label: cod-tnkrr
```

(sec-tnkrr-complejidad)=
### Complejidad y tiempos

Construir $A$ cuesta $O(n^2p)$ y cada iteración un producto matriz-vector $O(n^2)$, de modo que el entrenamiento es $O(n^2p+Tn^2)$ con memoria $O(n^2)$; la predicción de $m$ casos es $O(mnp)$. Con $T\ll n$ el costo es menor que el $O(n^3)$ de la factorización. En el ajuste final ($\alpha=0{,}0643$, $\gamma=0{,}0055$) el solver se detuvo por tolerancia en **30 iteraciones** con $\lVert r\rVert=0{,}400$ (`analisis/salidas/diagnostico_modelos.json`, leído del `.joblib` sin reentrenar). El refit tardó **0,047 s** frente a 0,078 s del KRR exacto, y la inferencia del test 0,0096 s. Con 30 iteraciones el costo del solver es del orden de $30n^2$ operaciones, frente a $n^3/3$ de la factorización de Cholesky: unas catorce veces menos. El refit es más rápido (0,047 s frente a 0,078 s), aunque en ambos modelos pesa también la construcción del kernel, $O(n^2p)$.

(sec-gprxgb)=
## Híbrido GPR–XGBoost con construcción OOF agrupada

(sec-gprxgb-r2)=
### Originalidad (R2) verificada en el código

`Precalculo/gpr_xgb_hpo_e3.py:104` define `GPRStackXGBRegressor(RegressorMixin, BaseEstimator)`. El GPR (`GaussianProcessRegressor`) y XGBoost (`XGBRegressor`) son de librería; lo propio es la **regla de combinación** (líneas 118-146) y la **construcción fuera del fold agrupada por estudiante** de las meta-variables (`_compute_stage`, líneas 65-81). Encaja en la fila «modelo híbrido no neuronal con al menos un componente central original» del Cuadro 1, que exige además una ablación (sección [](#sec-ablacion)).

(sec-gprxgb-formulacion)=
### Motivación y formulación

Un GPR exacto con ruido casi nulo interpola el entrenamiento: en este proyecto su RMSE de entrenamiento es 0,0386 y el kernel optimizado lleva el ruido blanco a su cota inferior ($10^{-5}$). Si XGBoost aprendiera el residuo **dentro de la muestra**, vería residuos casi nulos y no aprendería nada útil. Por eso las meta-variables se construyen fuera del fold. Con el kernel

$$
k_\theta(x,x')=C\big[\text{Matérn}_{5/2}(x,x')+\text{RBF}(x,x')\big]+\sigma_w^2\,\delta_{xx'},
$$ (eq-gpr-kernel)

cuyos hiperparámetros $\theta$ maximizan la verosimilitud marginal con cinco reinicios, el GPR da la media y la desviación posteriores {cite:p}`rasmussen2006`

$$
\mu(x)=k_\theta(x)^\top(K_\theta+\sigma^2 I)^{-1}y,\qquad
s^2(x)=k_\theta(x,x)-k_\theta(x)^\top(K_\theta+\sigma^2 I)^{-1}k_\theta(x).
$$ (eq-gpr-posterior)

Sean $\mathcal G_1,\dots,\mathcal G_5$ los folds de `GroupKFold` por estudiante **dentro de cada conjunto de ajuste**. Para el estudiante $i\in\mathcal G_j$, $\mu_i^{\text{oof}}$ y $s_i^{\text{oof}}$ provienen de un GPR ajustado sin $\mathcal G_j$. XGBoost $g$ aprende el residuo con las variables y las dos meta-variables, y la predicción suma ambas etapas:

$$
g=\arg\min_{g}\sum_{i}\big(y_i-\mu_i^{\text{oof}}-g(z_i)\big)^2+\Omega(g),\quad z_i=[x_i,\mu_i^{\text{oof}},s_i^{\text{oof}}],\qquad
\hat y(x)=\mu(x)+g\big([x,\mu(x),s(x)]\big),
$$ (eq-gprxgb)

donde en la predicción $\mu$ y $s$ salen de un GPR reajustado en todo el conjunto con $\theta$ fijo. Es una forma de *stacked generalization* {cite:p}`wolpert1992` con dos diferencias: el meta-modelo aprende el **residuo** (no una combinación de predicciones) y la partición interna respeta los grupos. Una advertencia de diseño: en entrenamiento $g$ ve $\mu^{\text{oof}}$ de GPR ajustados con el 80 % de los datos, mientras que en predicción recibe $\mu$ de un GPR con el 100 %; ese desajuste es inherente al apilamiento.

(sec-gprxgb-pseudocodigo)=
### Pseudocódigo

```{code-block} text
:caption: GPR–XGBoost con meta-variables OOF agrupadas.
:label: alg-gprxgb
Entradas: X (variables crudas), y, grupos (estudiante), hiperparámetros de XGBoost
Salidas:  GPR con kernel θ̂, XGBoost g
  1. si grupos no se entregan: error                     # sin grupos habría fuga
  2. para cada fold j de GroupKFold(5) por estudiante dentro de (X, y):
  3.     ajustar preprocesamiento y GPR en X[−j]; predecir μ, s en X[j]
  4. θ̂ ← kernel optimizado de un GPR ajustado en todo (X, y)
  5. Z ← preprocesar(X);  GPR_final ← GPR(θ̂ fijo, sin optimizar) ajustado en (Z, y)
  6. g ← XGBoost ajustado en [Z, μ_oof, s_oof] con objetivo y − μ_oof
Predicción para x*:
  7. (μ*, s*) ← GPR_final(x*);  ŷ ← μ* + g([z*, μ*, s*])
Parada: la del optimizador del GPR (L-BFGS, 5 reinicios) y n_estimators de XGBoost.
```

```{literalinclude} analisis/codigo/gpr_xgb_hpo_e3.py
:language: python
:lines: 104-146
:lineno-start: 104
:caption: Regla de combinación del híbrido (`Precalculo/gpr_xgb_hpo_e3.py`).
:label: cod-gprxgb
```

(sec-gprxgb-complejidad)=
### Complejidad y tiempos

Cada ajuste del GPR exacto cuesta $O(n^3)$ por evaluación de la verosimilitud y se repite por cada reinicio y fold interno; XGBoost con histograma cuesta aproximadamente $O(T\,n\,p')$ con $T$ árboles y $p'=69$ entradas. En la búsqueda, la etapa GPR se calcula **una vez por conjunto de ajuste** y se reutiliza entre candidatos (caché por contenido); por eso su costo no está en los tiempos por candidato. El refit final tardó **294,3 s** —tres órdenes de magnitud más que los kernels— y la inferencia del test 0,085 s. La búsqueda final de XGBoost con cinco estrategias sumó 764,7 s sin contar la etapa GPR.

(sec-pruebas-unitarias)=
## Pruebas unitarias

La guía exige cuatro propiedades verificadas con `pytest` (§5.4). Las pruebas preexistentes del proyecto cubrían solo una parte: `Precalculo/test_scopus_e3.py::test_estimators_roundtrip_and_mechanisms` comprueba el centrado aprendido y la serialización del KRR, y `Dash/test_original_models.py` verifica métricas y folds de todos los originales. No había pruebas del solver TN-KRR ni del híbrido. Se añadió `analisis/test_modelos_originales.py`, que usa **datos sintéticos** y no escribe en `resultados/` ({numref}`tab-pruebas-unitarias`).

:::{table} Pruebas unitarias de los tres originales y requisito de §5.4 que cubren.
:label: tab-pruebas-unitarias

| Requisito | KRR centrado | TN-KRR | GPR–XGBoost |
| --- | --- | --- | --- |
| (i) Aprende en un sintético con solución conocida | `…aprende_y_revierte_a_la_media`: RMSE < 0,1 y $\hat y\to\bar y$ lejos de los datos | `…reproduce_la_solucion_exacta`: coeficientes = $(K+\alpha I)^{-1}y$ (tolerancia 10⁻⁶) | `…aprende_y_usa_metavariables_oof`: RMSE < ½ DE(y) y 69 entradas en XGBoost |
| (ii) Reproducibilidad con la misma semilla | `…es_determinista_y_clonable` | `…es_determinista_y_clonable` | `…reproducible_con_semilla_y_clonable` |
| (iii) Entradas inválidas | `…rechaza_entradas_invalidas` (NaN, longitudes) | `…rechaza_hiperparametros_invalidos` (6 casos) y `…rechaza_datos_invalidos` | `…exige_grupos` (sin estudiante) |
| (iv) Compatibilidad con `clone` | `…es_determinista_y_clonable` | `…es_determinista_y_clonable` | `…reproducible_con_semilla_y_clonable` |
| Propiedad adicional | — | `…criterios_de_parada` (1 iteración; controles del artículo) | — |
:::

```{literalinclude} analisis/salidas/pytest_resumen.txt
:language: text
:caption: Resumen de `python -m pytest analisis -rA` (24 de octubre de 2026): incluye las pruebas de los análisis del libro.
:label: cod-pytest
```

(sec-ablacion)=
## Estudio de ablación

La ablación usa **solo predicciones OOF existentes** con los mismos folds ({numref}`tab-ablacion`, `analisis/pruebas_r3.py`); no se reentrenó nada.

```{include} analisis/tablas/ablacion.md
```

**GPR–XGBoost.** Retirar el GPR (XGBoost solo) empeora el error en 0,0125 puntos con una diferencia significativa (p BCa = 0,010): **el GPR es el componente que aporta**. Retirar XGBoost (GPR solo) **no empeora** el error: el GPR solo obtiene 0,8013 ± 0,0407 frente a 0,8028 del híbrido, una diferencia de +0,0016 a favor del GPR solo, no significativa (p = 0,23). La comparación tiene una salvedad: el GPR solo proviene de la ejecución histórica `resultados/e3/gpr_xgb/` con un reinicio del optimizador, mientras que el híbrido activo usa cinco; aun así, **la ablación no demuestra que la regla de combinación —el componente original— aporte una mejora medible**, que es lo que el Cuadro 1 exige para un híbrido.

**KRR centrado frente a TN-KRR.** La diferencia (−0,0047 a favor del KRR centrado; p BCa = 0,059) **mezcla dos cambios**: el solver (exacto frente a truncado) y el centrado del objetivo. La propiedad que distingue al centrado —revertir a la media y no a cero lejos de los datos— se verifica de forma aislada en la prueba unitaria `test_krr_centrado_aprende_y_revierte_a_la_media`.

(sec-convergencia-hpo)=
## Optimización de hiperparámetros y convergencia

Los hiperparámetros propios se optimizaron dentro de la validación anidada con los cinco métodos; la búsqueda final eligió **TPE** para el KRR centrado (`alpha` = 0,3002; `gamma` = 0,0104) y el TN-KRR (`alpha` = 0,0643; `gamma` = 0,0055), y **DEAP** para el GPR–XGBoost (226 árboles, `learning_rate` = 0,0033, 9 hojas, `reg_lambda` = 2,31).

```{figure} images/originales/hpo_convergencia_tpe_deap.png
:alt: Curvas de TPE y DEAP relativas al mejor punto del Grid en las seis búsquedas de cada modelo de la pestaña Originales.
:name: fig-convergencia-originales

Convergencia de TPE (verde) y DEAP (amarillo): mejor RMSE interno menos el mejor del Grid (puntos de nota) frente a evaluaciones; trazo fino = folds externos, grueso = búsqueda final.
```

La {numref}`tab-hpo-originales` detalla, para cada original, el RMSE interno de la búsqueda final y el costo de cada estrategia.

```{include} analisis/tablas/hpo_originales.md
```

Los dos kernels cuestan entre 2 y 9 s por búsqueda final; el GPR–XGBoost, entre 92 y 244 s, sin contar la etapa GPR compartida. En los tres, TPE o DEAP superan al mejor punto del Grid por milésimas, y Random y Halving —que comparten los mismos 16 candidatos— quedan entre 13 y 15 milésimas por detrás.

La [](#fig-convergencia-originales) es la curva de convergencia que pide la guía: TPE alcanza el nivel del Grid en menos de 12 evaluaciones y lo supera en milésimas en los dos kernels y en el híbrido, porque sus dominios continuos contienen valores que la grilla no tiene.

(sec-evaluacion-originales)=
## Ajuste en entrenamiento, validación y prueba

```{figure} images/originales/eval_m5.png
:alt: KRR centrado: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: fig-eval-krr

KRR centrado: nota predicha frente a real y residuos (puntos de nota) en los tres conjuntos.
```

```{figure} images/originales/eval_m19.png
:alt: TN-KRR: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: fig-eval-tnkrr

TN-KRR: mismo formato que la figura anterior.
```

```{figure} images/originales/eval_m15.png
:alt: GPR–XGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: fig-eval-gprxgb

GPR–XGBoost: mismo formato; en entrenamiento las predicciones caen sobre la diagonal porque el GPR interpola.
```

Las tres figuras muestran el mismo comportamiento. En validación la media por decil del residuo es casi plana (sin sesgo sistemático por nivel), la dispersión es mayor en predicciones bajas y las predicciones se comprimen hacia el centro. El KRR centrado predice 20 de 1.309 registros fuera de [0, 5], frente a 39 del SVM lineal. En el test los tres subestiman en promedio (residuo medio +0,14 a +0,15), señal de un cambio de nivel en 202530 que afecta también a los benchmarks. El GPR–XGBoost en entrenamiento ([](#fig-eval-gprxgb)) es un artefacto de interpolación, no un ajuste perfecto.

(sec-shap-originales)=
## Interpretabilidad: SHAP del original frente al mejor benchmark

Siguiendo el criterio del dashboard, SHAP se calcula para el **líder por RMSE medio de validación, el KRR centrado**, con un estimador de permutaciones antitéticas sobre el pipeline completo (64 caminos, 32 filas de referencia, semilla 42; aditividad con residuo máximo 9 × 10⁻¹⁶) en las 188 filas del test. El mejor benchmark, XGBoost, se explica con TreeSHAP exacto. Los métodos difieren, de modo que la comparación es de órdenes y magnitudes, no de valores exactos ({numref}`tab-shap-comparacion`).

```{include} analisis/tablas/shap_comparacion.md
```

```{figure} images/originales/shap_lider.png
:alt: KRR centrado: resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: fig-shap-krr

KRR centrado: resumen SHAP (aporte en puntos de nota por estudiante) y waterfalls del caso con menor y mayor error absoluto del test.
```

```{figure} images/clasicos/shap_xgboost.png
:alt: XGBoost: resumen SHAP en el test y waterfalls de dos casos.
:name: fig-shap-xgboost

XGBoost (mejor benchmark): resumen SHAP en puntos de nota y waterfalls de dos casos.
```

Ambos modelos coinciden en la variable principal, **Saber 11 · global** (23,1 % y 27,7 %), pero reparten el resto de forma distinta. El KRR distribuye la atribución de manera más uniforme y da peso a la división académica y la asignatura (9 % cada una), que XGBoost casi no usa (0,8 % y 0 %); XGBoost concentra la señal en el dominio inicial (16,6 %), el programa (16,4 %) y el avance por cuartiles (11,3 %). Como programa, división y asignatura están anidadas, y avance, dominios y cuartiles son redundantes ({ref}`sec-eda-bivariado`), las dos familias reparten la misma información entre variables correlacionadas. El caso de mayor error del test (registro 118: nota real 1,0; predicción 4,04) es el mismo en los dos modelos: un perfil de nota alta que nada en las 15 variables anticipa ([](#fig-shap-krr)). Las explicaciones describen el modelo, no causas.

(sec-comparacion-originales)=
## Comparación de los tres originales

:::{table} Resumen de los tres originales.
:label: tab-comparacion-originales

| | KRR centrado | TN-KRR | GPR–XGBoost |
| --- | --- | --- | --- |
| Parte propia (R2) | Centrado del objetivo; composición de librería, **sin clase propia** | Solver CG truncado en clase propia (NumPy) | Regla de combinación OOF agrupada en clase propia |
| Algoritmo de origen | KRR + {cite:t}`eckhard2014` | {cite:t}`maalouf2014` | {cite:t}`de2026` |
| RMSE externo (media ± DE) | **0,8010 ± 0,0419** | 0,8056 ± 0,0453 | 0,8028 ± 0,0429 |
| RMSE test (descriptivo) | 0,9091 | 0,9096 | **0,9029** |
| Refit final / inferencia test | 0,078 s / 0,0096 s | 0,047 s / 0,0096 s | 294,3 s / 0,085 s |
| Ablación | Frente a TN-KRR sin centrar: −0,0047 (p = 0,059) | Frente a KRR exacto centrado: +0,0047 (p = 0,059) | El GPR aporta (−0,0125 frente a XGBoost solo); la regla de combinación no mejora al GPR solo |
| Pruebas unitarias (4 de §5.4) | Completas | Completas + parada | Completas |
:::

La {numref}`tab-comparacion-originales` resume la tensión central del capítulo: el modelo con **menor error** (KRR centrado) es el de **parte propia más débil**, y el modelo con la **parte propia más elaborada** (GPR–XGBoost) no demuestra en la ablación que esa parte aporte. El TN-KRR tiene una implementación propia sólida y verificada contra la solución exacta y, aunque es el de mayor error de los tres, supera al SVM lineal en los cinco folds. El {ref}`sec-validacion` contrasta estadísticamente los tres frente a los benchmarks.
