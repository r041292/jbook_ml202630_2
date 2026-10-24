:::{table} Matriz de novedad: búsquedas ejecutadas el 24 de octubre de 2026 (`analisis/busqueda_literatura.py`).
:label: tab-matriz-novedad

| Id | Base de datos | Cadena de búsqueda | Result. | Revis. | Relev. | Observación |
| --- | --- | --- | ---: | ---: | ---: | --- |
| S1 | OpenAlex | `"kernel ridge" AND ("student performance" OR "academic performance" OR "exam score" OR grade)` | 13 | 13 | 2 | Ahmed et al. (2022) usan KRR como comparador para la nota de Matemáticas de Ingeniería; Cherfane et al. (2026) incluyen kernel ridge en un ensamble que predice el MCAT. Ninguno centra el objetivo. |
| S1 | arXiv | `all:"kernel ridge" AND (all:student OR all:academic OR all:grade)` | 4 | 4 | 0 | Teoría de KRR y aplicaciones ajenas (dosis, finanzas). |
| S1 | Semantic Scholar | `"kernel ridge" AND ("student performance" OR "academic performance" OR "exam score" OR grade)` | 10 | 10 | 2 | Los mismos dos estudios cercanos que en OpenAlex. |
| S2 | OpenAlex | `"kernel ridge" AND (centering OR centred OR centered OR "mean-centered" OR intercept) AND target` | 11 | 11 | 0 | Centrado en otros sentidos (kernels condicionados, química); sin educación. |
| S2 | arXiv | `all:"kernel ridge" AND (all:centering OR all:centered OR all:intercept)` | 14 | 14 | 1 | Elkhalil et al. (2019) analizan la «centered KRR» (KRR con desplazamiento) en alta dimensión; teoría, sin aplicación educativa. |
| S2 | Semantic Scholar | `"kernel ridge" AND (centering OR centred OR centered OR "mean-centered" OR intercept) AND target` | 11 | 11 | 0 | Sin trabajos educativos ni de centrado del objetivo en KRR. |
| S3 | OpenAlex | `"truncated Newton" AND "kernel ridge"` | 2 | 2 | 2 | Maalouf y Homouz (2014) proponen TN-KRR; Abdulla et al. (2022) lo aplican a porosidad de SS316L. |
| S3 | arXiv | `all:"truncated Newton" AND all:"kernel ridge"` | 0 | 0 | 0 | Sin resultados. |
| S3 | Semantic Scholar | `"truncated Newton" AND "kernel ridge"` | 2 | 2 | 2 | Los mismos dos trabajos que en OpenAlex. |
| S4 | OpenAlex | `"kernel ridge" AND ("conjugate gradient" OR "truncated Newton") AND (student OR academic OR education)` | 0 | 0 | 0 | Sin resultados. |
| S4 | arXiv | `all:"kernel ridge" AND all:"conjugate gradient" AND (all:student OR all:education)` | 0 | 0 | 0 | Sin resultados. |
| S4 | Semantic Scholar | `"kernel ridge" AND ("conjugate gradient" OR "truncated Newton") AND (student OR academic OR education)` | 0 | 0 | 0 | Sin resultados. |
| S5 | OpenAlex | `"Gaussian process" AND (XGBoost OR "gradient boosting") AND ("student performance" OR "academic performance" OR grade)` | 25 | 25 | 2 | Retno et al. (2024) usan GP y XGBoost por separado para clasificar notas finales; Shen y Shen (2026) comparan 18 algoritmos de rendimiento académico. Ningún registro revisado describe un híbrido GPR–XGBoost. |
| S5 | arXiv | `all:"Gaussian process" AND (all:XGBoost OR all:"gradient boosting") AND (all:student OR all:academic)` | 0 | 0 | 0 | Sin resultados. |
| S5 | Semantic Scholar | `"Gaussian process" AND (XGBoost OR "gradient boosting") AND ("student performance" OR "academic performance" OR grade)` | 14 | 14 | 0 | Aplicaciones de ingeniería y salud; ninguna educativa. |
| S6 | OpenAlex | `"Gaussian process" AND XGBoost AND (residual OR stacking OR hybrid)` | 162 | 25 | 4 | Híbridos GP–XGBoost en baterías (Hu et al., 2026), turbinas (Janani y Sasikala Reddy, 2025), corrección de residuos en concreto (Rai et al., 2026) y pandeo de cascarones (De et al., 2026). |
| S6 | arXiv | `all:"Gaussian process" AND all:XGBoost AND (all:residual OR all:stacking OR all:hybrid)` | 5 | 5 | 1 | De et al. (2026), el preprint de referencia del híbrido GPR–XGBoost. |
| S6 | Semantic Scholar | `"Gaussian process" AND XGBoost AND (residual OR stacking OR hybrid)` | 78 | 25 | 2 | De et al. (2026) y un ensamble eólico con corrección de error por GP. |
| S7 | OpenAlex | `(precalculus OR "placement test" OR ALEKS) AND ("machine learning" OR prediction) AND (grade OR exam OR performance)` | 69 | 25 | 3 | Predicción de notas con pruebas de ubicación (Şen et al., 2012; Madison et al., 2014) y con un test de precálculo; métodos estadísticos o de minería de datos, ninguno con KRR, TN-KRR ni GPR–XGBoost. |
| S7 | arXiv | `(all:precalculus OR all:ALEKS OR all:"placement test") AND (all:"machine learning" OR all:prediction)` | 40 | 25 | 0 | Coincidencias por «ALEKS» y «prediction» en física y química. |
| S7 | Semantic Scholar | `(precalculus OR "placement test" OR ALEKS) AND ("machine learning" OR prediction) AND (grade OR exam OR performance)` | 61 | 25 | 2 | Estudios de rendimiento en cursos remediales y de matemáticas sin los modelos propuestos. |
| S8 | OpenAlex | `("regresión ridge" OR "proceso gaussiano" OR "procesos gaussianos" OR kernel) AND ("rendimiento académico" OR "desempeño académico") AND (predicción OR "aprendizaje automático")` | 2 | 2 | 2 | Dos estudios en español de éxito académico con regresión logística, SVM, RF y MLP; sin KRR ni GPR–XGBoost. |
| S8 | Semantic Scholar | `("regresión ridge" OR "proceso gaussiano" OR "procesos gaussianos" OR kernel) AND ("rendimiento académico" OR "desempeño académico") AND (predicción OR "aprendizaje automático")` | 1 | 1 | 1 | El mismo estudio peruano de 2022. |
:::
