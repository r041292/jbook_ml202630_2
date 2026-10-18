# Cinco búsquedas para SVM y los seis clásicos

Implementación del 18 de octubre de 2026. Se conservan el código, los artefactos
y los resultados del Grid Search E3 anterior. La ejecución nueva está versionada
en `resultados/e3/busquedas/<run_id>/` y solo se activa cuando está completa.

## Protocolo

Se mantiene la partición real E3: 1.309 registros de train, agrupados en 1.293
estudiantes; 188 registros de test temporal 202530. Mismos cinco folds externos
que el SVM histórico y cinco folds internos por estudiante. Se conservan reglas
de negocio y outliers válidos. IDs, periodo y nota_final no son predictores.

En **cada entrenamiento externo**, las cinco estrategias evalúan RMSE medio
en sus mismos cinco folds internos. Se elige la configuración válida de menor
RMSE a fidelidad completa, incluyendo candidatos de todas las estrategias;
equivale a comparar sus mejores candidatos. Empates dentro de 1e-12 se resuelven
por orden preestablecido Grid, Random, TPE, DEAP y Halving. No se usan ni el
fold externo ni el test para esa selección. Después se repite todo el proceso
en train completo, sin copiar los parámetros que rindieron mejor en test.

Cada evaluación crea **manualmente un pipeline nuevo por fold interno** con
`pipeline_for(key).set_params(...)`, ajusta el preprocesamiento y el modelo
exclusivamente en el entrenamiento de ese fold y transforma su validación sin
volver a ajustar. Esto se implementa en `manual_fold`, tanto para TPE como para
fitness evolutivo y las demás estrategias. Hay aserciones de grupos disjuntos;
el test no forma parte de la API del optimizador. La caché de fitness solo
reutiliza duplicados dentro del mismo método, fold externo y fidelidad.

Se conservan las preparaciones anteriores: SVM/KNN/Ridge/Lasso con
mediana/log1p/escalado y moda/one-hot; Random Forest con mediana/moda/ordinal
sin escalado; XGBoost con categorías nativas; Decision Tree con mediana/moda y
one-hot completo sin escalado. Todas se aprenden dentro de fit.

## Métodos y presupuestos fijados antes de ejecutar

| Estrategia | Configuración |
| --- | --- |
| Grid Search | ParameterGrid exhaustivo con todos los puntos del grid histórico |
| Random Search | 16 sorteos con semilla 42; categorías/enteros uniformes, continuos uniformes o loguniformes |
| Bayesiana | Optuna5.0.0, TPESampler independiente, 20 ensayos, 6 iniciales aleatorios y 24 candidatos para EI |
| Genética | DEAP1.4.3, población8, generación inicial más3 generaciones, torneo 3,1 élite |
| Multi-fidelidad | Successive Halving manual,16→8→4 candidatos, factor2,25/50/100% grupos de train interno |

**TPE y adquisición.** El surrogate es Tree-structured Parzen Estimator:
modela densidades l(x) de configuraciones buenas y g(x) de las restantes.
Se justifica TPE por los dominios mixtos de categorías, enteros y continuos
logarítmicos, sin definir un kernel GP ni distancias ordinales entre categorías.
La adquisición aproxima Mejora Esperada (Expected Improvement) mediante
l(x)/g(x); no se usa GP, UCB ni PI. Los seis ensayos iniciales aleatorios
priorizan exploración; las propuestas posteriores explotan regiones
prometedoras mediante densidades probabilísticas y muestreo, manteniendo
exploración. Veinte ensayos no demuestran convergencia.
EI busca disminuir el mejor RMSE mediante la ganancia esperada, en lugar de
usar solo la probabilidad de mejora (PI) o una cota de confianza (UCB).
[Referencia oficial Optuna](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html).

**Operadores DEAP.** Torneo3 controla presión selectiva sin requerir fitness
positiva, útil al minimizar RMSE. Cruce uniforme: probabilidad por pareja 0.8 y
por gen 0.5, sin suponer cercanía ordinal entre categorías. Mutación por reinicio
uniforme: probabilidad por individuo 0.3 y por gen 1/d, donde d es el número de
hiperparámetros. Los genes normalizados se decodifican al dominio y a escala
logarítmica cuando corresponde. Elitismo 1 preserva el mejor individuo y deja
7 puestos para variación. La población pequeña limita el coste, pero puede
converger prematuramente; no se declara convergencia solo por estancamiento.

Se registran por generación mejor/media de fitness, fracción de configuraciones
fenotípicas únicas y entropía Shannon media normalizada de genes. Para continuos
se usan 10 intervalos; enteros/categorías mantienen sus valores. La combinación
de pérdida de diversidad y estancamiento indica posible convergencia prematura.
Se guardan las trayectorias tanto por fold externo como en train completo.
[Referencia oficial DEAP](https://deap.readthedocs.io/en/master/api/tools.html).

**Fidelidad y reducción.** La fidelidad es fracción de estudiantes completos
del entrenamiento interno, con subconjuntos anidados determinados sin consultar
el objetivo. La validación interna siempre está completa y fija. Se vuelve a
ajustar todo el pipeline en cada ronda; no se transfiere un imputador entrenado
en la ronda anterior. Esta fidelidad sirve a todos los regresores, incluidos
los que no tienen árboles ni épocas. Factor2 ofrece una eliminación moderada
con dos oportunidades de reevaluación. Solo los cuatro supervivientes al 100%
pueden ganar la selección conjunta. Una configuración buena a presupuesto
completo puede ser eliminada prematuramente por el ranking parcial.

El presupuesto de filas de entrenamiento es aproximadamente 12 evaluaciones
completas equivalentes (16×.25+8×.5+4×1), frente a 16 de Random, sin sumar tiempos
paralelos ni prometer ahorro de pared: Halving realiza más fits y su coordinación
puede dominar en este conjunto pequeño.
[Eliminación sucesiva](https://scikit-learn.org/stable/modules/grid_search.html#successive-halving).

## Espacios de búsqueda

Se preservan todos los grids anteriores. Los otros métodos exploran los
intervalos siguientes, que también contienen los valores del grid:

| Modelo | Dominio estocástico |
| --- | --- |
| SVM | C loguniforme[.01,10]; epsilon uniforme[0,1] |
| KNN | vecinos entero[5,101]; weights uniform/distance; p1/2 |
| Ridge | alpha loguniforme[.01,1000] |
| Lasso | alpha loguniforme[.0001,.1] |
| Random Forest | árboles entero[150,500]; profundidad4/6/8/12/None; mínimo hoja entero[2,20] |
| XGBoost | árboles entero[150,500]; profundidad entero[1,6]; learning_rate loguniforme[.01,.1] |
| Decision Tree | profundidad2/3/4/6/8/None; mínimo hoja entero[2,30]; ccp_alpha uniforme[0,.01] |

No es una comparación de algoritmos a igual presupuesto. Grid explora puntos
discretos; los otros métodos exploran dominios más densos y tienen presupuestos
distintos. Se documentan los ensayos efectivamente evaluados, incluyendo
duplicados reutilizados y fallos; no se afirma óptimo global.

## Tiempos, evidencia y activación

Antes de ejecutar se instrumentaron segundos de pared con perf_counter.
`TIEMPOS_EJECUCION.md` conserva búsqueda por método/fold externo/final,
refits e inferencia. La búsqueda excluye refit e incluye preparación, scoring,
coordinación y registro. Los fits/predict internos por fold figuran en los JSONL
de ensayos, incluidos en la búsqueda: sus tiempos paralelos no se suman como
duración de pared. Cuatro procesos loky y un hilo por proceso, CPU; métodos,
ensayos y modelos se ejecutan secuencialmente. Una inferencia por lote, sin
calentamiento explícito; carga/E/S fuera de predict. No se elige modelo por tiempo.

`seleccion_antes_test.json` se guarda después de cerrar las siete selecciones y
antes de inferir sobre test. Se verifican los pipelines serializados contra sus
predicciones. El test ya se había consultado antes: su reevaluación es
descriptiva, no una nueva prueba ciega. La comparación de familias por CV externa
sigue siendo exploratoria. Los contrastes históricos de Originales conservan
su SVM y sus predicciones originales, explícitamente identificados en pantalla.

La curva de aprendizaje SVM usa grupos completos y los parámetros elegidos
en su train externo; los mantiene fijos para las submuestras. Se documenta como
curva condicional, sin nueva HPO por fracción. Cada fit y predict se registra.

```powershell
.\Precalculo\venv\Scripts\python.exe -m pip install -r .\Precalculo\requirements_busquedas_e3.txt
.\Precalculo\venv\Scripts\python.exe .\Precalculo\evaluar_busquedas_e3.py
.\Precalculo\venv\Scripts\python.exe .\Precalculo\activar_busqueda_e3.py <run_id_completo>
.\Precalculo\venv\Scripts\python.exe .\Dash\run_measured.py .\Dash\prepare_data.py
```

La sincronización del dashboard lee `resultados/e3/busqueda_activa.json` solo
si la carpeta referida tiene `completo.json`; los resultados anteriores no se
sobrescriben. Tras activar la ejecución, usar `Dash/run_measured.py` para preparar
la caché y validar. Las fichas clásicas y la búsqueda SVM muestran métodos,
dominios, RMSE interno, elección final, evolución genética y tiempos de búsqueda,
entrenamiento/refit, con referencia histórica Grid preservada. La inferencia
se conserva por lote en la evidencia técnica y el registro central.

## Ejecución completa y activa · 20261018_102325_af643f83

El18-oct-2026 terminó la ejecución completa:210 búsquedas,22650 fits internos,
57 refits(incluye15 ajustes de curva SVM),131 inferencias de pipelines.
Auditoría de todos los fits:0 grupos compartidos,0 discrepancias de partición
entre métodos a igual fidelidad y0 fits fallidos. Total directo3484.5797877s,
desde creación del registro hasta exportación final, después de cargar/verificar
particiones; no sumar con tiempos parciales. CPU/procesos/hilos/versiones y
mediciones crudas: TIEMPOS_EJECUCION.md y tiempos/20261018_102325_af643f83.

| Modelo | Método final | RMSE interno de selección | RMSE medio CV externa | RMSE test |
| --- | --- | ---: | ---: | ---: |
| SVM lineal | Bayesiana TPE | 0.82107342 | 0.82410557 | 0.92989217 |
| KNN | Genética DEAP | 0.84811869 | 0.85504495 | 0.92388988 |
| Ridge | Bayesiana TPE | 0.82434295 | 0.82526555 | 0.91704090 |
| Lasso | Genética DEAP | 0.82723652 | 0.82882457 | 0.91973077 |
| Random Forest | Grid Search | 0.82790769 | 0.82971516 | 0.93963518 |
| XGBoost | Bayesiana TPE | 0.80807512 | 0.81558148 | 0.91370821 |
| Decision Tree | Random Search | 0.90263399 | 0.89483020 | 1.01041093 |

Friedman de las nuevas predicciones OOF: χ²=17.828571428571, gl6, p=0.006675192720. Lectura global exploratoria, sin ganador por pares.

Los siete parámetros finales quedaron guardados antes de evaluar test. Los
Grid Search finales reproducen los RMSE de selección históricos; la selección
conjunta puede mejorar ese criterio sin mejorar test o todos los folds externos.
Los resultados no justifican superioridad general por una diferencia pequeña
de selección. Originales conserva sus artefactos idénticos byte a byte.
