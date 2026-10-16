# Opciones de regresión sin deep learning: búsqueda en Scopus

Fecha: 2026-10-15. Investigación exploratoria mediante la sesión de Chrome autorizada por el usuario. Se consultaron registros de Scopus y textos de editoriales/autores cuando estuvieron accesibles. No es una revisión sistemática ni se ejecutaron nuevos modelos. Se permiten librerías listas para usar.

## Contexto de selección

El histórico canónico tiene 14 modelos contando SVM y Dummy. Ya se probaron LinearSVR, KNN, Ridge, Lasso, Random Forest, XGBoost, logicDT adaptado, TabPFN original y ajustado, RIM adaptado, TCR-XGBoost, TabICLv2 y HRT-Boost oficial. Se excluyen de las propuestas nuevas. CatBoost, XBART, PILOT/coPILOT, Kernel Ridge y SVR RBF no aparecen entre los métodos evaluados.

Referencia temporal E3: RMSE SVM lineal 0.927706; XGBoost 0.906274; mejor estimación puntual observada TabICLv2 0.897815. Ningún candidato previo mejora significativamente frente a SVM después de Holm. El test ha sido consultado repetidamente: futuras comparaciones tendrán carácter exploratorio.

## Búsqueda reproducible

Se usó el campo «Article title, Abstract, Keywords» de Scopus y orden por relevancia. Las cifras son las observadas durante la sesión, pueden variar y se solapan; no representan artículos leídos.

1. `regression AND (XGBoost OR "support vector regression") AND ("Gaussian process" OR "Bayesian additive regression trees" OR "model tree" OR "kernel ridge" OR CatBoost)`; 4448 resultados inicialmente, 4093 al limitar 2020–2026.
2. `XBART OR (PILOT AND "regression tree") OR (NGBoost AND "natural gradient boosting") OR "fast weighted linear model trees"`; 216 resultados con el filtro de años de la búsqueda anterior.
3. `XBART OR (PILOT AND "regression tree") OR "fast weighted linear model trees"`; 58 resultados, inicialmente 2020–2026.
4. Tras limpiar filtros: `CatBoost AND "unbiased boosting"`; 7 resultados, incluido el artículo original de 2018.
5. `"RaFFLE" AND "linear"`; 11 resultados sin un registro pertinente del método en los resultados examinados. Esto no demuestra ausencia de indexación. No se presenta RaFFLE como publicación Scopus verificada en esta búsqueda.

## Candidatos prioritarios

### 1. XBART: ensamble bayesiano de árboles

He, J.; Hahn, P. R. **Stochastic Tree Ensembles for Regularized Nonlinear Regression**. JASA 118(541), 2023. DOI publicado online en 2021.

- [Registro Scopus 85112688498](https://www.scopus.com/pages/publications/85112688498)
- [Artículo publicado](https://doi.org/10.1080/01621459.2021.1942012)
- [Manuscrito de los autores consultado, junio de 2021](https://jingyuhe.com/files/scalabletrees.pdf)
- [Código original](https://github.com/JingyuHe/XBART)

Combina regularización bayesiana y construcción estocástica de árboles. En la tabla 3 del manuscrito obtiene menor RMSE que XGBoost ajustado por CV en cuatro de siete conjuntos reales: AirQuality, BiasCorrection, ElectricalStability y GasTurbine. Por ejemplo, ElectricalStability: 0.0091 frente a 0.0173; pierde en otros conjuntos. Son promedios de 20 particiones aleatorias por conjunto, no un protocolo temporal por estudiante. Es la evidencia comparativa más directamente pertinente encontrada; no prueba una mejora en Precálculo. El sitio de la editorial mostró verificación de seguridad y se recurrió al manuscrito público del autor, sin eludir esa verificación. La compatibilidad del código original con Windows y el entorno compartido queda pendiente.

### 2. CatBoost: alternativa práctica para datos mixtos

Prokhorenkova et al. **CatBoost: unbiased boosting with categorical features**. NeurIPS 2018.

- [Registro Scopus 85063596785](https://www.scopus.com/pages/publications/85063596785)
- [Publicación oficial](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html)
- [Documentación del algoritmo](https://catboost.ai/docs/en/concepts/algorithm-main-stages_fighting-biases)

Utiliza boosting y estadísticas ordenadas para categorías, lo que ofrece una hipótesis razonable para nuestras siete variables categóricas. No es una red neuronal aunque se publique en NeurIPS. Su evidencia de mejora sobre otros boosters no equivale a demostrar menor RMSE en nuestro problema; el benchmark principal del artículo es de clasificación. Probar CatBoostRegressor con pérdida RMSE, categorías nativas y preparación aprendida dentro del fold sería un experimento nuevo y de integración relativamente sencilla. No introducir el identificador de estudiante como categoría predictora.

### 3. Kernel Ridge / TN-KRR: alternativa regularizada no lineal

Abdulla, H.; Maalouf, M.; Barsoum, I.; An, H. **Truncated Newton Kernel Ridge Regression for Prediction of Porosity in Additive Manufactured SS316L**. Applied Sciences 12(9), 4252, 2022.

- [Registro Scopus 85129163440](https://www.scopus.com/pages/publications/85129163440)
- [Artículo](https://doi.org/10.3390/app12094252)

El resumen indexado informa mejor MSE y R² de KRR frente a Ridge y SVR en predicción de porosidad. No compara con XGBoost y trabaja con cuatro predictores de fabricación: la transferencia a estudiantes es una hipótesis. KRR con kernel RBF representa relaciones no lineales y conserva regularización; no duplica Ridge lineal. Con 1309 registros de entrenamiento, la matriz kernel es viable. Truncated Newton describe el procedimiento numérico: usar KernelRidge convencional sería probar la familia, no reproducir exactamente TN-KRR. En esta sesión se verificaron ficha y resumen, no todas las tablas del texto completo.

### 4. PILOT / coPILOT: modelos lineales por regiones

Raymaekers, J.; Rousseeuw, P. J.; Verdonck, T.; Yao, R. **Fast linear model trees by PILOT**. Machine Learning 113, 6561–6610, 2024.

- [Registro Scopus 85197662746](https://www.scopus.com/pages/publications/85197662746)
- [Texto completo consultado](https://doi.org/10.1007/s10994-024-06590-3)

Debois, F.; Raymaekers, J.; Servotte, T.; Verdonck, T. **Fast weighted linear model trees**. Advances in Data Analysis and Classification, publicado 23 de junio de 2026.

- [Registro Scopus 105042634645](https://www.scopus.com/pages/publications/105042634645)
- [Texto completo consultado con acceso institucional](https://doi.org/10.1007/s11634-026-00683-8)
- [Código de los autores](https://github.com/STAN-UAntwerp/wPILOT)

PILOT ajusta relaciones lineales dentro de una estructura de árbol; resulta atractivo cuando una relación global aproximadamente lineal cambia entre subpoblaciones. coPILOT promedia dos árboles complementarios: el segundo pondera más los casos mal predichos por el primero. Ofrece flexibilidad e interpretabilidad.

Limitación decisiva: sección 4.1 de coPILOT restringe XGBoost a DOS árboles. Su superioridad allí no demuestra que supere al XGBoost completo ya ajustado. PILOT original compara con CART, FRIED, M5, Ridge y Lasso, no con XGBoost. Tampoco copiar su selección de hiperparámetros sobre la misma CV usada para informar resultados: nuestro experimento conservaría CV anidada. No usar las ponderaciones transductivas por covariate shift del artículo en el test reservado; para el primer experimento basta coPILOT ordinario. Ponderar errores no genera observaciones sintéticas.

## Opciones secundarias verificadas en Scopus

| Método / publicación | Fuente | Motivo para posponer |
|---|---|---|
| GA-BART: Hourly streamflow forecasting using a Bayesian additive regression tree model hybridized with a genetic algorithm (Journal of Hydrology, 2022) | [Scopus 85123004249](https://www.scopus.com/pages/publications/85123004249), [DOI](https://doi.org/10.1016/j.jhydrol.2022.127445) | Resumen informa mejoras frente a GA-SVR en hidrología, con excepciones por horizonte; no comparación XGBoost. No asumir el papel exacto del algoritmo genético sin revisar métodos. |
| Multikernel GPR + SVR: Electricity Price Prediction Using Multikernel Gaussian Process Regression Combined With Kernel-Based Support Vector Regression (Journal of Forecasting, 2026) | [Scopus 105030988089](https://www.scopus.com/pages/publications/105030988089), [DOI](https://doi.org/10.1002/for.70124) | Combina predicciones GPR y SVR. Evidencia del resumen frente a LASSO autorregresivo y DNN; no demuestra superar XGBoost/SVR aislado. Adaptar kernels eléctricos al problema académico requeriría justificarlo. |
| GS-BART: Bayesian Additive Regression Trees with Graph-Split Decision Rules (JASA, 2026) | [Scopus 105044210603](https://www.scopus.com/pages/publications/105044210603), [DOI](https://doi.org/10.1080/01621459.2026.2655550) | Requiere grafos con significado; actualmente no tenemos una estructura de red o espacial justificada. |
| NGBoost: Natural Gradient Boosting for Probabilistic Prediction (ICML/PMLR 119, 2020) | [Scopus 105021993724](https://www.scopus.com/pages/publications/105021993724) | Atractivo para distribuciones e incertidumbre; su objetivo probabilístico no garantiza mejorar RMSE. |

Estos cuatro registros se verificaron mediante sus fichas/resúmenes; no se presentan como reproducciones auditadas de sus experimentos completos. Se excluyen las variantes neuronales de la recomendación principal.

## Orden recomendado y protocolo futuro

Por pertinencia científica de la comparación: XBART primero. Por facilidad de integración y categorías disponibles: CatBoost es el primer experimento práctico. Después KRR RBF y coPILOT. Añadir SVR RBF como control económico: el baseline actual es LinearSVR y aún no cubre kernels no lineales.

Cada experimento conservaría fuente real sin aumento, reglas de negocio, 15 predictores, objetivo nota_primer_parcial, exclusión nota_final/pidm, periodo test 202530, purga por estudiante, GroupKFold externo/interno y métricas RMSE/MAE/MAPE/R². La codificación y escalado pueden variar según el estimador, ajustados exclusivamente en el fit correspondiente. Seleccionar por train; informar diferencia pareada frente a SVM y XGBoost, IC y p con corrección por la familia completa de contrastes declarada. Ningún artículo garantiza significancia en los 188 estudiantes de test; una cohorte futura ofrecería confirmación más sólida.

Esta tarea solo documenta opciones. No se modificaron notebooks, modelos, datos fuente, resultados ni dashboard.
