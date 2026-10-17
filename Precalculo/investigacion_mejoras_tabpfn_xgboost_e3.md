# Opciones enfocadas en mejorar TabPFN y XGBoost · 2026-10-15

## Actualización: librerías listas autorizadas por el usuario

El usuario retiró expresamente la restricción de no usar librerías listas.
Este es el criterio vigente para las opciones y las implementaciones futuras;
ya no se necesita una excepción por modelo. Se solicitan opciones para elegir,
no ejecutar ni instalar modelos todavía.

Primera ronda recomendada, como juicio de encaje y no pronóstico de mejora:

1. **CatBoostRegressor**: candidato práctico inicial para8 numéricas y7
   categóricas, categorías nativas sin one-hot externo y opción Ordered.
   Comparar explícitamente Ordered/Plain, profundidad moderada y regularización
   en CV interna. No inferir que supera XGBoost en esta cohorte por sus benchmarks.
   [Categorías oficiales](https://catboost.ai/docs/en/features/categorical-features),
   [paper original](https://arxiv.org/abs/1706.09516).
2. **TabICLv2, TabICLRegressor**: modelo fundacional distinto de TabPFN con
   checkpoint de regresión tabicl-regressor-v2-20260212.ckpt. El artículoICML2026
   reporta ventajas en TabArena/TALENT frente a RealTabPFN2.5; no implica mejora
   local. Paquete tabicl listo, CPU soportada y GPU aconsejable para inferencia
   grande. Empezar sin fine-tuning. Auditar preprocesamiento interno/outlier
   clipping para conservar todos los registros válidos del proyecto.
   [Artículo](https://proceedings.mlr.press/v306/qu26a.html),
   [repo/API](https://github.com/soda-inria/tabicl).
3. **LightGBM LGBMRegressor(linear_tree=True)**: modelos lineales en hojas,
   particiones usuales; categorías solo en splits y numéricos en regresiones
   locales. Comparar con LightGBM convencional como control. Escalado numérico
   recomendado para la variante lineal, hojas grandes y regularización. No
   presentarlo como LinXGBoost exacto. Mayor memoria que LightGBM convencional,
   pero estructura razonable para1309 filas.
   [Parámetro oficial](https://lightgbm.readthedocs.io/en/latest/Parameters.html#linear_tree).

Segunda ronda opcional:

- **HRT-Boost / HRTBoostingRegressor**: vuelve a ser elegible. Paquete oficial
  con árboles oblicuos lineales, optimización de nodos y boosting. La garantía
  de descenso del riesgo empírico no garantiza generalización. Revisar estabilidad
  y limitar profundidad/capacidad para esta muestra pequeña.
  [Artículo](https://arxiv.org/abs/2605.23422),
  [librería oficial](https://github.com/Hongyi-Li-sz/HRT-Boost).
- **TabM**: disponible en paquete oficial tabm y en interfaces de pytabkit para
  regresión. Ensamble eficiente de MLPs, entrenado desde cero para nuestro problema,
  distinto del esquema preentrenado TabPFN. Más riesgo de sobreajuste con1309 filas;
  early stopping/selección deben usar grupos explícitos.
  [Paquete](https://github.com/yandex-research/tabm),
  [interfaces](https://github.com/dholzmueller/pytabkit).
- **AutoGluon Tabular**: AutoML/stacking de varios modelos, no algoritmo individual.
  Útil después de identificar bases nuevas y diversas. Mayor coste de memoria,
  disco/dependencias y cuidado con splits automáticos. La API estable groups usa
  LeaveOneGroupOut: no pasar1293 IDs esperando5 folds. Para reproducir los folds
  canónicos se usarían etiquetas de los folds internos ya generados, excluidas
  como predictor. Verificar API de la versión elegida y todos los holdouts del
  stacking; no dejar que el sistema elija particiones por filas ni vea test.
  [API oficial](https://auto.gluon.ai/stable/api/autogluon.tabular.TabularPredictor.html).

No se instala ningún paquete ni se entrenan modelos en esta actualización. Al
seleccionar, resolver compatibilidad con el venv compartido, pin de versiones,
configuración de regresión y memoria local. Mismas15 variables, limpieza,
outliers conservados, test202530 y CV5x5 por estudiante; preparación específica
por modelo y todo ajuste aprendido solo en fit. Preferir tres candidatos
predefinidos antes de volver a examinar test; mantener carácter exploratorio
del test ya usado y no prometer significancia.

## Búsqueda anterior bajo el criterio retirado (conservar como historial)

Solicitud anterior: proponer alternativas para que el usuario elija; no implementar ni
entrenar otro modelo en esta búsqueda. Se mantiene la preferencia por métodos
sin una librería Python lista, aceptando código de referencia. La excepción
previamente solicitada para TabPFN se identifica expresamente.

## Evidencia local que orienta la selección

CV externa agrupada: TabPFN2.5 RMSE0.807118, XGBoost0.814264, Ridge0.824343,
SVM0.826140. Test202530: TabPFN0.898277, XGBoost0.906274, SVM0.927706.
El fine-tuning local de TabPFN no mejoró su resultado original. RIM y logicDT
tampoco superaron los mejores métodos. No hay mejora significativa favorable
frente al SVM tras Holm sobre la familia conocida de nueve candidatos.

Diagnóstico adicional solo sobre OOF, sin tocar test: correlación de residuos
TabPFN/XGBoost0.9744, TabPFN/Ridge0.9572, TabPFN/SVM0.9515,
XGBoost/Ridge0.9439, XGBoost/SVM0.9324, Ridge/SVM0.9895.
Procedencia: train.csv.gz, clasicos/train_predictions.csv.gz y
tabpfn_25/train_predictions.csv.gz de resultados/e3. No se ajustaron pesos de
un ensamble ni se evaluó un nuevo predictor. La correlación alta reduce el
atractivo de promediar sin más TabPFN y XGBoost; no prueba que todo ensamble
sea inútil ni sustituye una evaluación anidada.

## 1. TCR-XGBoost: primera prioridad metodológica

TCR calcula sensibilidad/robustez local de la relación entre predictores y
objetivo, reduce el peso de regiones menos robustas y vuelve a entrenar
XGBoost. El artículo evalúa el procedimiento en20 datasets de regresión.
Fuente: [artículo publicado](https://link.springer.com/article/10.1007/s10994-024-06704-x),
[scripts oficiales](https://github.com/montymaxzuehlke/tcr).

Encaje propuesto: aprovechar nuestro XGBoost ya competitivo, conservando todas
las filas reales con pesos positivos. No confundir una región poco robusta con
un error de datos. La ponderación podría perjudicar casos raros legítimos;
por ello evaluar RMSE normal sin ponderación y revisar subgrupos. El cálculo
de robustez y sus parámetros deben aprenderse solo en fit de cada fold.

Grilla inicial sugerida (no ejecutada): fracción reponderada .05/.10/.20,
factor de peso .3/.6/.9, más control sin reponderar. Distancia sobre preparación
numérica/categórica aprendida en fit; XGBoost puede mantener categorías nativas.
Esfuerzo estimado medio; cómputo relativo bajo/medio para1309 filas. El repo es
un pipeline de investigación, no un estimador empaquetado identificado. Esta
comprobación no demuestra inexistencia universal de librerías.

## 2. LinXGBoost: boosting con hojas lineales regularizadas

Extiende el criterio de boosting para estimar funciones lineales regularizadas
en hojas, en lugar de constantes. Cuenta con experimentos de regresión y código
de referencia NumPy. No equivale a poner Ridge al final de un CART cualquiera.
Fuentes: [artículo](https://arxiv.org/abs/1710.03634),
[referencia](https://github.com/ldv1/LinXGBoost).

Encaje propuesto: combinar la estructura por regiones de los árboles con
efectos continuos lineales. Que Ridge sea competitivo en nuestra CV hace que
esta sea una hipótesis razonable, no una predicción de mejora. Evitar muchas
variables dummy y hojas pequeñas; considerar solo numéricos en modelos locales
y usar categorías para particiones como adaptación explícita si se elige así.

Grilla propuesta: profundidad1/2, mínimo de hoja80/150, regularización1/10/100
y learning_rate.03/.1, con presupuesto acotado de rondas. Esfuerzo medio/alto,
CPU moderado. El repo consultado presenta archivos de referencia sin packaging
de una distribución Python identificado; no afirmar que no existe ningún
paquete alternativo. La familia amplia de hojas lineales sí está disponible en
otras librerías: aquí el candidato sería el procedimiento exacto de LinXGBoost.
El repo declara CC BY-NC-ND4.0; preferir implementación propia del artículo en
vez de modificar y redistribuir directamente su código.

## 3. Portfolio local de TabPFN2.5: extensión práctica, excepción identificada

Comparar checkpoint default y small-samples, codificación categórica nativa
como variante explícita de preparación y ensambles de8/16 estimadores frente
a los4 actuales. El modelo small-samples está dirigido a menos de3000 filas;
los autores advierten que los checkpoints alternativos son experimentales y
peores en promedio. Fuentes: [model card oficial](https://huggingface.co/Prior-Labs/tabpfn_2_5),
[README oficial SDK6.4.1](https://github.com/PriorLabs/TabPFN/blob/v6.4.1/README.md).

No es un nuevo algoritmo libre de librerías: usa la excepción de TabPFN ya
autorizada. La selección y agregación podrían escribirse localmente sin usar
AutoTabPFN, que sí es una solución lista. Mantener fuente, limpieza, variables
y particiones; la representación nativa sustituiría el one-hot como tratamiento
específico del modelo, registrado y comparado en CV interna. No aumentar datos
del curso ni cambiar sus notas. Sin un nuevo fine-tuning completo de pesos.

Esfuerzo bajo/medio, coste alto de CV en CPU. La prioridad práctica se apoya en
que TabPFN ya lidera nuestra CV; un checkpoint alternativo no garantiza mejora.
Elegir candidatos y pesos exclusivamente dentro de cada fit externo, evitando
la selección interna aleatoria por filas de paquetes automáticos.

## 4. XGBoost por clusters: alternativa experimental

Un artículo2025 propone particionar features con K-means/bisecting K-means y
entrenar un GBT por cluster. Usar XGBoost como experto sería una adaptación.
Fuente: [artículo](https://link.springer.com/article/10.1186/s40537-025-01071-3).
Es una opción de la búsqueda anterior que permanece sin probar, ahora enfocada
en extender el XGBoost existente. No se identificó librería del procedimiento
completo; K-means y XGBoost sí son componentes disponibles.

Puede capturar relaciones distintas entre perfiles, sin reutilizar el índice
de etiquetas de RIM. Principal riesgo: fragmentar1309 filas y sobreajustar.
Comparar K1 (global), K2 y K3, clusters con mínimo suficiente de estudiantes y
modelo global de respaldo. El clustering se ajusta solo en fit. Esfuerzo medio,
CPU bajo/medio. Menor prioridad que TCR por el tamaño pequeño de la muestra.

## Opciones revisadas y no priorizadas

- [HRT-Boost](https://github.com/Hongyi-Li-sz/HRT-Boost): encaje interesante,
  pero tiene pyproject.toml, pip install -e . y HRTBoostingRegressor listo;
  no cumple el criterio estricto de esta lista.
- [BoostPFN](https://proceedings.mlr.press/v258/wang25d.html) y
  [LoCalPFN](https://www.cs.toronto.edu/~guangweiyu/pdfs/localpfn.pdf): la evidencia
  original revisada corresponde a clasificación; extenderlos a regresión2.5
  sería otra adaptación, no una mejora de regresión ya validada por esos papers.
- [Q-aggregation causal](https://pypi.org/project/metacausal/0.2.1/): existe una
  clase empaquetada; no presentar el concepto como inequívocamente libre de
  librerías aunque la aplicación ordinaria de regresión tenga diferencias.
- Un promedio simple TabPFN+XGBoost no es primera prioridad por la correlación
  alta de sus residuos OOF. Los métodos de ensembling genéricos también tienen
  implementaciones listas; no renombrarlos como algoritmo nuevo propio.

## Decisión sugerida y evaluación

Empezar por TCR si prima un artículo de regresión y una implementación propia.
Si prima exprimir el mejor predictor existente, elegir primero el portfolio
TabPFN bajo la excepción ya identificada. LinXGBoost es el siguiente cambio de
arquitectura a considerar. Estas prioridades son inferencias de encaje, no
evidencia de una ganancia local aún no medida.

Seleccionar por CV5x5 por estudiante con RMSE sin pesos, comparar también MAE,
MAPE y R², mantener SVM como referencia primaria y TabPFN como mejor predictor
actual. No tratar folds como observaciones independientes para un t-test.
Fijar un candidato antes de consultar test; mientras se reutilice202530, toda
inferencia sigue siendo exploratoria y se debe conservar la familia acumulada.
Una confirmación fuerte requiere una cohorte nueva reservada. Ningún método
garantiza una reducción significativa, aunque mejore el RMSE puntual.
