# Dashboard · Entregable 3

## Navegación liviana y carga bajo demanda

Solo se envía la pestaña seleccionada. Las fichas, tablas de detalle, búsquedas,
diagnósticos y SHAP/LIME se cargan al abrir sus desplegables; al cerrarlos sus
gráficos se desmontan del navegador. Los filtros y pestañas se conservan durante
la sesión. No se recortan observaciones ni se cambian métricas/modelos.

`lazy_content.py` difiere los cuerpos de `html.Details`, incluidos los anidados.
Los cuerpos se guardan por hash en `Dash/.ui_cache/`, caché descartable de UI
compartida entre workers del mismo servicio, excluida de Git y del paquete.
Las factorías estáticas de búsquedas construyen tablas/curvas únicamente al
abrirse; no ejecutan fit/predict. Nunca usar `validation_layout` con el árbol
completo, pues volvería a enviarlo al cliente. Los callbacks SHAP requieren
que su contenedor esté montado; abrir filtros no solicita SHAP oculto.

Las respuestas JSON admiten gzip sin dependencias nuevas. Medición local del
esqueleto inicial:1.167.572→10.867bytes,2.572bytes con gzip (no incluye librerías
JS,imágenes o análisis solicitados después). Esqueleto de pestaña clásica10.231
bytes yOriginales9.572bytes;comparaciones/gráficos activos llegan por sus propios
callbacks. Los desplegables cerrados no incluyen sus tablas/figuras en el DOM.

## Originales actualizado · 19-oct-2026

Originales alinea sus tres etapas estadísticas con Clásicos: Friedman/MCS
exploratorios sobre25modelos con OOF, y25comparaciones por estudiante contra
el SVM activo con bootstrap-t,ICBCa yHolm25. Dummy y TabPFN fine-tuned no entran
al ómnibus; este último sí conserva su comparación exploratoria en test.
Los contrastes históricos se archivan y no se reutilizan con predicciones nuevas.

SVR RBF,Kernel Ridge RBF yTR-KRR completaron cinco búsquedas anidadas. SVM y
clásicos reutilizan las búsquedas vigentes; costosos/fijos se identifican. Líder
CV:Kernel Ridge RBF,RMSE0.8009641. Solo ese modelo recibe SHAP aproximado por
permutaciones yLIME,con resumen global ydoscasos test. No se elige por test.
Resultados versionados en originales_busquedas/ y activados mediante puntero,
sin sobrescribir históricos. Filtros de interpretabilidad reutilizan valores
guardados; no disparan nuevos fits/predict.

Protocolo,alcances,comandos ylista de12pendientes con tamaño de rejilla:
[Originales · multibúsqueda](../Precalculo/originales_busquedas_e3.md).

## Actualización de búsqueda · SVM y seis clásicos

Se añade a Grid Search una comparación anidada con Random Search, Optuna/TPE,
DEAP y Successive Halving manual. Cada entrenamiento externo selecciona método
y parámetros solo con sus cinco folds internos; train completo repite la
comparación para el refit final. Solo compiten candidatos a fidelidad completa,
por RMSE; el tiempo no decide. Se conservan reportes, predicciones y código E3
anteriores. Originales mantiene su inventario y SVM históricos, identificado
en pantalla, sin mezclar sus contrastes con las nuevas predicciones.

Las fichas clásicas y «Resultados de las cinco búsquedas en train · selección
y tiempos» en SVM documentan surrogate TPE/EI, exploración/explotación,
operadores DEAP/probabilidades/población/elitismo, diversidad por generación y
fold, fidelidad de grupos anidados y factor de reducción. Incluyen resultados
por estrategia, configuración elegida y tiempos de búsqueda y refit. La inferencia
permanece registrada por lote en la evidencia técnica y el documento central.
El mapa de Grid Search sigue visible; su mejor punto puede diferir del ganador
conjunto. Más detalles: [protocolo y reproducción](../Precalculo/busquedas_e3.md).

Nuevas ejecuciones versionadas: `resultados/e3/busquedas/<run_id>`. La caché lee
`busqueda_activa.json` únicamente con `completo.json`; los artefactos históricos
no se sobrescriben. Los tiempos crudos se conservan en `TIEMPOS_EJECUCION.md`,
`tiempos/` y en los JSONL de ensayos/folds. Los tiempos internos paralelos están
incluidos en la búsqueda y no se suman como pared. Test reutilizado: descriptivo,
no nueva evaluación ciega. Los presupuestos/espacios difieren entre métodos;
no es una comparación de eficiencia con presupuesto uniforme ni garantiza óptimo.

```powershell
.\Precalculo\venv\Scripts\python.exe -m pip install -r .\Precalculo\requirements_busquedas_e3.txt
.\Precalculo\venv\Scripts\python.exe .\Precalculo\evaluar_busquedas_e3.py
.\Precalculo\venv\Scripts\python.exe .\Precalculo\activar_busqueda_e3.py <run_id_completo>
.\Precalculo\venv\Scripts\python.exe .\Dash\run_measured.py .\Dash\prepare_data.py
```

La activación de una nueva ejecución se realiza después de verificar todos los
modelos; ejecutar el evaluador por sí solo no cambia el tablero en curso.

El flujo activo usa datos reales, test 202530 y GroupKFold anidado por estudiante.
Modelos predictivos se organiza en Split y CV, Modelos lineales, Clásicos y Originales.
Ejecutar también Precalculo/modelos_clasicos.py después de entregable3.py y antes
 de prepare_data.py para evaluar KNN, Ridge, Lasso, Random Forest y XGBoost.
Para añadir Decision Tree sin reentrenar esos modelos, ejecutar después
`Precalculo/evaluar_decision_tree_e3.py` y sincronizar con
`python Dash/run_measured.py Dash/prepare_data.py` usando el entorno compartido.
Protocolo, resultados y reproducción: [Decision Tree E3](../Precalculo/decision_tree_e3.md).
El notebook nuevo precalculo_modelos_clasicos_e3.ipynb inspecciona esos resultados.
Desde la raíz ejecutar entregable3.py, Dash/prepare_data.py y Dash/app.py usando
Precalculo/venv/Scripts/python.exe. Resultados en Precalculo/resultados/e3/.
No ejecutar actualizar_analisis.py: los notebooks anteriores permanecen intactos.
El trabajo vigente del dashboard continúa en main; los Books publicados
son antecedentes y se producirá uno nuevo. Ver CONTEXT.md para la reproducción completa.

## SHAP global y local en Modelos clásicos

`shap_xgboost.py` amplía la interpretabilidad de XGBoost, el menor RMSE medio
CV externa de la ejecución activa, sin atribuirle superioridad estadística
confirmada. Usa TreeSHAP exacto nativo de XGBoost: `pred_contribs=True`,
`approx_contribs=False`, CPU. No requiere instalar `shap`. Se transforma con el
pipeline guardado y se respeta el vocabulario de categorías aprendido en train.
La referencia implícita es el cover de las rutas de los árboles de entrenamiento
(tree-path-dependent), no un fondo construido con test. No reentrena.

El summary plot interactivo incluye las 15 variables y todos los puntos de
las 1.497 filas válidas por defecto (1.309 train + 188 test), sin muestrearlas.
Se puede cambiar a train o test y aplicar los filtros académicos. En train se
explica el modelo final, no OOF; no es una evaluación de generalización.
Orden por media |SHAP| y tabla de proporciones sobre suma de medias absolutas.
Azul/rojo representan valores numéricos bajos/altos normalizados por variable;
las categorías se muestran grises para no inventar un orden. Los valores son
los que recibió el árbol tras la imputación; jitter con semilla42 solo visual.

Dos waterfalls incluyen base, los15 aportes completos y predicción, junto con
la nota real como referencia: menor y mayor error absoluto en test (dentro de
los filtros, empates por orden anónimo). La selección es ilustrativa, posterior
a la evaluación; no elige modelo ni parámetros. No se inventa un umbral de
«clasificación correcta» para regresión. Si el filtro tiene menos de2 casos
test, se informa la limitación. Lecturas automáticas describen aportes positivos,
negativos y diferencias entre casos; no interpretan SHAP como causa del error.
Un desplegable compara con el LIME existente: sustituto lineal ponderado frente
a atribuciones aditivas de Shapley, exactitud/aproximación, fondo, correlaciones,
interacciones y vecindarios imposibles. Los números anónimos permiten inspeccionar
los mismos casos en LIME; los pesos de condiciones LIME no son SHAP intercambiables.

En cada arranque se calculan una vez los SHAP completos y se reutilizan en
callbacks, sin nuevas inferencias al filtrar. Se verifican las188 predicciones
test guardadas (atol1e-12) y base+suma SHAP=predicción en1497 filas (atol1e-5,
por float32). El primer cálculo registró residuo máximo5.852431e-6 puntos.
`TimingRun` instrumenta antes de ejecutar: transformación/DMatrix, inferencia
del pipeline, TreeSHAP, validación y total (no sumar con etapas). Configuración,
hashes, entorno, estado/fallos y duraciones quedan en `tiempos/` y en el registro
central; no se registran valores de personas. Sin búsquedas ni refits.

Fuentes: [SHAP](https://arxiv.org/abs/1705.07874),
[TreeExplainer y referencias de dependencia](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html),
[XGBoost · contribuciones](https://xgboost.readthedocs.io/en/stable/prediction.html),
[LIME](https://arxiv.org/abs/1602.04938).

## Comparación estadística ampliada de Modelos clásicos

La etapa3 contiene «Seis comparaciones frente al SVM · test por estudiante»,
después de las comparaciones de finalistas y antes de los efectos por fold.
La tabla principal se ordena por ΔMSE ascendente.
Se usan predicciones guardadas de los seis clásicos y el SVM: media de errores
cuadráticos por estudiante, pesos iguales entre estudiantes. No se filtra la
familia por MCS ni se usa Friedman de CV como puerta de estos contrastes test.
Bootstrap-t bilateral centrado bajo H0,49.999 réplicas/semilla20261018, índices
emparejados entre los siete modelos, SD muestral y p=(1+excedencias)/(B+1).
Holm sobre los seis p; α0.05. IC BCa95 individuales de ΔMSE y ΔRMSE, con
jackknife retirando estudiantes completos. Cohen d_z descriptivo sobre las
diferencias MSE. BCa degenerado no se sustituye silenciosamente. Los IC no son
simultáneos ni son duales del contraste bootstrap-t: pueden excluir0 sin que
Holm detecte diferencia. Se conservan diagnósticos de SE cero y error Monte Carlo.

Fuente privada: `load_partitions()` reconstruye los grupos por ID y valida
fila a fila predictores/objetivo/periodo con el test activo y sus hashes. Los IDs
solo se usan en memoria y no llegan al dashboard. Solo se exporta el resumen
`data/clasicos/comparacion_svm_bootstrap.json`, con procedencia/hashes.
Regenerar desde raíz con `Precalculo/venv/Scripts/python.exe -X utf8 Dash/student_comparison.py`;
también se regenera al preparar datos. La CLI registra el artefacto nuevo en
manifest.json. No entrena ni ejecuta predict. Carga del dashboard verifica
hashes de datos/código; la exportación futura incluye el módulo y el JSON.

Evidencia de cada preparación: resultados.json y distribuciones_bootstrap.npz
en tiempos/<analysis_run>, más metadatos/eventos y TIEMPOS_EJECUCION.md.
No se sobrescribe el historial; el JSON de caché señala la ejecución activa.
Resultado actual:188estudiantes/188registros; ninguna diferencia con p Holm<0.05.
Decision Tree p crudo0.01666, Holm0.09996; Lasso p crudo0.16564, Holm0.8282;
KNN/Ridge/Random Forest/XGBoost Holm1. El IC BCa individual de Lasso excluye0,
igual que el de Decision Tree; no contradice la ausencia de significancia familiar.
Alcance exploratorio posterior a revisión de test202530, modelos finales fijos,
supone independencia entre estudiantes y no verifica independencia por clase/
cohorte. No incluye variabilidad de entrenamiento ni otros periodos. No se
reelige familia o hiperparámetros con estos resultados. Los históricos de CV,
MCS y bootstrap previo se conservan.

La sección principal de Clásicos presenta las conclusiones, tabla ómnibus,
MCS exploratorio (α = 0.10), pares de finalistas, tamaños del efecto e IC del
95 % de RMSE. La documentación metodológica se puede desplegar. Solo se muestra
inferencia con Todos en ambos filtros; cambiar los gráficos entre CV/test no
cambia el alcance CV del contraste. No hay selección por test.

`classic_posthoc.py` calcula MCS T_R/eliminación e_R sobre MSE por fold
(RMSE²), con pesos iguales y 3.125 remuestreos emparejados exhaustivos de los
cinco folds; centra bajo H0, reutiliza índices y acumula p por máximo monótono.
Pérdidas idénticas dan t=0; diferencias constantes no nulas dan t infinito.
No requiere otra dependencia ni ajusta/predice con modelos. La aproximación
NO corrige la dependencia entre entrenamientos solapados y NO garantiza
cobertura nominal del 90 %. No es un conjunto confirmatorio defendible.
El rechazo de Friedman a α=0.05 habilita este post hoc exploratorio; sin rechazo,
no se calcula MCS ni se generan sus pares.

Ejecución activa 20261018_102325_af643f83: Friedman χ²=17.828571428571,
gl=6, p=0.006675192720. MCS exploratorio conserva XGBoost (p=1), SVM lineal
y Ridge (ambos p=0.7664); sus tres IC por folds de ΔMSE incluyen cero.
GW/CW y DM-HLN figuran no aplicables: no hay secuencia de pronósticos,
horizonte definido ni diseño condicional/anidamiento establecido para CW.
GW puede admitir tanto modelos anidados como no anidados bajo sus condiciones.
No se trata el orden de filas o folds como tiempo, ni se fabrica un bootstrap
estacionario. Los p crudos DM y su ajuste Holm permanecen no aplicables. El bootstrap por
folds de diferencias es exploratorio, no estacionario ni simultáneo/corregido
por selección del MCS; no captura incertidumbre de reentrenamiento.

Se muestran los 21 pares con Cliff marginal (25 cruces de pérdidas) y Cohen
emparejado d_z (media/SD muestral de las cinco diferencias MSE); negativos
favorecen A. No se afirma simetría con cinco observaciones ni relevancia práctica
por umbrales no acordados; SD cero queda no estimable. Los IC de métricas en
test reutilizan el bootstrap por estudiante ya exportado (1.000 réplicas,
pipelines fijos), separados del post hoc CV. No hay ganador confirmado por pares.

Validar con `Precalculo/venv/Scripts/python.exe -X utf8 Dash/run_measured.py --tests`.
La suite registra cualquier fit/predict que ejecute en el registro central de
tiempos, incluido el sustituto LIME; el análisis estadístico usa resultados
guardados y no reentrena los siete modelos.

Referencias: [MCS](https://doi.org/10.3982/ECTA5771),
[GW](https://doi.org/10.1111/j.1468-0262.2006.00718.x),
[CW](https://www.kansascityfed.org/documents/5368/pdf-RWP05-05.pdf),
[DM-HLN](https://doi.org/10.1016/S0169-2070(96)00719-4).

## Comparación histórica de Modelos clásicos con Friedman

Este bloque describe la ejecución Grid anterior, conservada para trazabilidad.
En la ejecución multibúsqueda, tablas, rangos, Friedman y bootstrap se recalculan
desde sus predicciones/folds nuevos; las cifras activas se consultan en el tablero
y en el informe de la carpeta versionada.

Solo concursan siete modelos: KNN, Ridge, Lasso, Random Forest, XGBoost, Decision Tree y SVM
lineal. Dummy se excluye de tablas, gráficos, rangos, Friedman y bootstrap
mostrados en esta sección; los artefactos canónicos se conservan completos.
`classic_friedman.py` usa los35 RMSE de esos modelos en los cinco folds externos
emparejados, con rangos por fold (menor RMSE = rango1; empates promediados).
χ²17.485714286, gl6, p asintótico0.007654544: se rechaza H0 a α0.05;
el resultado global no identifica diferencias entre pares. Cinco folds no satisfacen la
recomendación de SciPy para el p χ²; además los entrenamientos se solapan.
Lectura exploratoria. Test y subgrupos conservan métricas descriptivas.

No se aplica Friedman a pares modelo–SVM: la implementación exige tres o más
modelos. Wilcoxon sería un contraste distinto y exige diferencias independientes;
no se añade sobre estos cinco folds solapados. ΔRMSE vs SVM sigue siendo
una diferencia descriptiva. No hay post hoc ni p-valores por pares nuevos.
Solo se entrenó el nuevo árbol; los demás modelos conservan sus ajustes.
Decision Tree usa mediana numérica, moda y one-hot completo, sin escalado ni
log1p. Su grid de profundidad, mínimo por hoja y poda se ajusta en train;
test no selecciona parámetros. Se incluye en tablas, barras, rangos,
bootstrap, diagnósticos, filtros y simulador. El inventario Originales se conserva.
Tiempos de búsqueda/refit/inferencia: `../TIEMPOS_EJECUCION.md` y `../tiempos/`;
no se añaden componentes visuales de tiempo.
Fuentes: [Friedman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.friedmanchisquare.html)
y [Wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).

## Diagnósticos de residuos en Modelos lineales

La tabla añade `p-valor (White)` y `p-valor (BDS)` para Dummy/SVM en validación
OOF reunida y test, recalculados con los filtros. Las métricas conservan sus
definiciones; los p OOF no son medias de p por fold. La gráfica comparativa
solo muestra RMSE/MAE; R² permanece en la tabla.

White usa LM con las ocho numéricas originales, constante, cuadrados e
interacciones, casos completos sin imputar; no incluye categóricas. Escalado
y eliminación QR de dependencias exactas estabilizan el cálculo sin cambiar
el espacio auxiliar. Mínimo30 casos y10 grados de libertad residuales. BDS
usa dimensión2, epsilon=1.5 DE muestral, mínimo30 residuos y orden del CSV
conservado al filtrar. Su hipótesis es IID, no independencia aislada, y ese
orden no constituye una trayectoria temporal individual. Rechazar IID no
identifica cuál de los dos supuestos falla. OOF reúne distintos ajustes.

Son diagnósticos exploratorios sin ajuste múltiple ni corrección por registros
repetidos por estudiante, y no se usan para elegir modelos. No rechazar no prueba
los supuestos. El desplegable muestra estadísticos, n, parámetros y motivos de
casos no estimables. No se cambian fuentes, predicciones ni modelos.

Fuentes oficiales: [White](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.het_white.html)
y [BDS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.bds.html).

## Contrastes del EDA y presentación

Cada filtro recalcula las evidencias sobre train disponible: Shapiro–Wilk
(W, p, n) en notas y densidades; Kruskal–Wallis (H, gl, p y medianas)
en cajas; χ² frente a proporciones iguales en categorías observadas; Q de
Cochran para los indicadores de ausencia emparejados por registro. No se
imputan valores ni se usa test. Los grupos pequeños/constantes tienen
estados explícitos sin inventar estadísticos.

Cada tarjeta categórica identifica la prueba chi-cuadrado de bondad de ajuste
y resume la comparación de conteos. La introducción conjunta define χ², gl y p,
sin repetir aclaraciones extensas en cada gráfica.

Spearman se justifica por el interés en asociaciones monotónicas y el uso de
rangos, con menor sensibilidad a magnitudes extremas. No se decide por un
p de normalidad. Para la variable elegida, se compara con Pearson mediante
Δ = ρ − r, bootstrap de pares completos (1999 réplicas, semilla 42, rangos
recalculados), IC95% percentil y p bilateral aproximado de la distribución
centrada bajo H₀. No mide superioridad de un método. La matriz ofrece ρ, n,
p bilateral y Holm sobre todos sus pares estimables: p asintótico con n > 500,
permutación (1999 réplicas, corrección +1) con n ≤ 500.

Inferencia exploratoria: filas independientes es una aproximación; no hay
IDs en la caché para corregir dependencia por estudiante. Solo la familia
de la matriz tiene ajuste múltiple y no cubre la búsqueda entre filtros.
Los χ² categóricos usan uniformidad como referencia explícita, sin exigir
equilibrio institucional; Q usa aproximación χ², limitada con ausencias raras.
No se interpreta un resultado no significativo como equivalencia o normalidad.

Las dos tarjetas de correlación presentan conclusiones visibles que siguen
los filtros: variable elegida frente a la nota, dirección y coeficiente Spearman;
y variables/pares con mayor asociación en valor absoluto en la matriz. Sus
explicaciones extensas se conservan en desplegables cerrados por defecto.
Se retira de la interfaz el apartado histórico sobre una elección de Pearson.

Las tarjetas explican cada contraste con «¿Qué revisa/compara?» y una lectura
del resultado. La comparación pareada se define como calcular ρ y r con los
mismos registros y restarlos. La tabla distingue «p sin ajuste (Spearman)» de
«p ajustado (Holm)»: ambos prueban asociación Spearman frente a cero; ninguno
es el p de comparar métodos. Los notebooks EDA anteriores revisados calculaban
ambos coeficientes, sin documentar una elección de Pearson como más apropiado.

Fuentes: documentación oficial de SciPy para
[Shapiro–Wilk](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.shapiro.html),
[Kruskal–Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html),
[Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html),
[bootstrap pareado](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).

`display_labels.py` presenta código y nombre en controles, gráficos, hover,
textos y tablas. Los códigos originales siguen en filtros, datos y modelos.
Fuentes CSS +3 px, gráficos 15 px (hover 16), con densidades en dos columnas
y una en pantallas estrechas. `eda_statistics.py` no añade dependencias.

## Interpretación del pipeline, betas y XGBoost

Al final de Split y CV se muestra el flujo del pipeline compartido por LinearSVR,
Ridge y Lasso: mediana, log1p en tiempos/tasa, StandardScaler, moda y one-hot con
referencia. El número de columnas, estadísticas y referencias se leen del
artefacto guardado. Se distingue fit en train de transform en validación/test.

El reporte completo de betas y su CSV se ordenan por |β| descendente. Incluye
intercepto y referencias en cero, interpretación por desviación estándar, cambios
en unidades originales y la fórmula exacta de log1p. Son asociaciones matemáticas
condicionales, sin p inventados; avance y dominios no pueden variarse independientemente.

Clásicos incorpora LIME para el XGBoost guardado (no cambia con el selector de
familia). Permite elegir un caso anónimo de test o train y respeta los filtros.
En train explica el ajuste final, nunca su predicción OOF. Los parámetros del
explicador usan solo train, sin usar notas de test ni reentrenar XGBoost.

Por defecto se usa una **variante empírica**: remuestreo de filas completas de
train y núcleo/regresión local de la librería LIME. Se conservan las relaciones
de las filas observadas, pero puede faltar soporte cercano al caso. Se ofrece
también LIME estándar con perturbaciones independientes y diagnóstico de
coherencia dominios/avance. Esta comprobación no valida todas las restricciones.
Semilla42, cuartiles y todos los15 términos. Se muestran predicción XGBoost,
aproximación LIME, error local, fidelidad R² ponderada y descomposición aditiva.
Ese R² es ajuste del sustituto sobre su vecindario, no rendimiento predictivo ni
validación externa. Un R² alto puede coexistir con un error grande en el caso.
Los aportes no son causas ni importancia global; semilla fija no garantiza
estabilidad ante otras semillas. Las explicaciones se generan solo al pulsar el
botón y se limpian al cambiar caso/filtros/método. Dependencia:lime==0.2.0.1.

Referencias: [artículo LIME](https://arxiv.org/abs/1602.04938),
[API oficial](https://lime-ml.readthedocs.io/en/latest/lime.html) y
[tutorial de regresión](https://marcotcr.github.io/lime/tutorials/Using%2Blime%2Bfor%2Bregression.html).

## Comparación vigente: CV externa y test temporal

**Kernel Ridge RBF** es el candidato activo con menor RMSE medio de CV externa
(0.801325). Su pipeline original guardado reproduce las188 predicciones de test
(error máximo1.3e-15), sin reentrenamiento. La sección de exploración y el
simulador usan ese artefacto. Abre en OOF; RMSE reunido0.802245 difiere de la
media entre folds0.801325. Las tablas y gráficos siguen RMSE ascendente.

Se añade **Truncated Newton KRR RBF** al inventario de modelos originales:
RMSE medio CV0.809646, OOF0.810569 y test2025300.907802. Frente al SVM lineal,
su contraste CV da ΔRMSE−0.016494, p=0.168940 y Holm25=1.000000. Está disponible en
comparaciones, diagnósticos, correlación de errores y simulador. Kernel Ridge
RBF exacto sigue como líder CV. En test, TR-KRR vs SVM da ΔRMSE−0.019903,
p=0.12010/Holm2=0.24020; vs XGBoost, ΔRMSE+0.001529,
p=0.90418/Holm2=0.90418. Este suplemento Holm2 cubre solo las dos referencias
de TR-KRR y permanece separado de la familia global de test Holm55; ninguno de
los contrastes del test es significativo.

GPR sola se retiró del inventario activo, la inferencia CV, la matriz de errores
y el simulador por solicitud del usuario. Se conservan los antecedentes
archivados; el híbrido GPR–XGBoost permanece como experimento distinto.
La familia **Holm25 CV vs SVM** incluye los25 competidores con OOF frente al SVM;
se conserva también al mostrar solo Clásicos. Kernel Ridge
p=0.16475/Holm25=1.00000 y TR-KRR p=0.16894/Holm25=1.00000. Ninguna mejora
evaluada es significativa después de Holm25.

La t pareada corregida por solapamiento (aproximación Nadeau–Bengio) usa5 folds
sin repeticiones y4 grados de libertad: inferencia exploratoria de baja potencia,
sin garantía de calibración exacta para GroupKFold. Test202530 se mantiene como
contraste temporal; no selecciona familias. No se trasladan p globales a filtros.
TabPFN fine-tuned carece de CV independiente. Los p/familias de test se conservan
como inferencia histórica separada. No se entrena al arrancar el dashboard.

Ver [README E3](../Precalculo/README_E3.md) y
[método y resultados CV](../Precalculo/resultados/e3/cv_externa/README.md).
Desde la raíz, con el entorno compartido:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Precalculo\significancia_cv_externa_e3.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe -m unittest discover -s Dash -p 'test_*.py'
```

## Documentación histórica

# Dashboard de Precálculo

## Publicar en Render con GitHub

Repositorio: https://github.com/r041292/jbook_ml202630_2, rama `main`.
El checkout de publicación local está en `../RenderDeploy/`. Contiene únicamente
el código, los assets, los datos derivados sin IDs ni nota_final y cinco fuentes
públicas de resultados/texto. Los datos brutos con nombres/correos y los notebooks
no se publican. El historial anterior de Precalculo permanece en su repositorio local.

En Render, usar **New > Blueprint**, conectar GitHub y seleccionar este repositorio.
Render lee `render.yaml` y crea `precalculo-dashboard` con plan Free. Revisar el
servicio y confirmar su creación. Esperar estado Live y abrir su URL HTTPS.

También se puede usar **New > Web Service** con estos valores:

| Campo | Valor |
| --- | --- |
| Branch | `main` |
| Language | Python 3 |
| Root Directory | Vacío (raíz del repositorio) |
| Build Command | `pip install -r Dash/requirements.txt` |
| Start Command | `gunicorn --chdir Dash app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile -` |
| Health Check Path | `/healthz` |
| Instance Type | Free |
| Auto Deploy | On Commit |
| Environment | `PYTHON_VERSION=3.12.14`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` |

No seleccionar `Dash` como Root Directory: Render excluye los archivos externos
a ese directorio y el tablero necesita `Precalculo/`. No entrenar ni ejecutar
notebooks durante el build. Los artefactos ya ajustados están versionados.
El paquete verifica hashes de todos los artefactos y de las cinco fuentes públicas
antes de servir solicitudes; las fuentes completas se verifican al exportar localmente.
`.gitattributes` conserva los bytes de los archivos para no alterar esos hashes.

El plan Free suspende el servicio tras 15 minutos sin tráfico; la siguiente visita
puede demorar aproximadamente un minuto. No necesita base de datos ni disco persistente.

Para publicar una actualización, ejecutar las pruebas locales, exportar y subir:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_deployment.py
git -C RenderDeploy add Dash Precalculo render.yaml .python-version .gitattributes .gitignore
git -C RenderDeploy commit -m "Actualiza dashboard de Precalculo"
git -C RenderDeploy push origin main
```

La regeneración de datos se realiza en el espacio local completo, siguiendo el
procedimiento descrito abajo. El checkout público sirve el modelo ya ajustado.

Tres pestañas: Introducción, EDA (variables, aumentación y exploración) y Modelos lineales.
Filtros combinables por programa/asignatura y gráficos interactivos con descarga PNG.
Incluye contraste gráfico de aumentación con originales, densidades numéricas,
frecuencias categóricas, cajas de nota por dominio final y conclusiones con tratamientos.
Modelos incorpora el reporte completo de coeficientes y un acordeón para predecir
con el pipeline ajustado. LinearSVR no define p-valores; esa limitación se muestra
en el reporte, junto a las categorías de referencia.

## Iniciar

Desde `C:\Users\Rubiel\Documents\Machine Learning Maestria`:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\app.py
```

Abrir [dashboard local](http://127.0.0.1:8050/). Detener con Ctrl+C en la terminal del servidor.
Desde `Dash`, usar `..\Precalculo\venv\Scripts\python.exe app.py`.
Antes de reiniciar, detener la instancia existente. Mantener un solo servidor en
el puerto 8050 para que el navegador muestre siempre la versión actualizada.

## Dependencias y preparación

Las dependencias ya están instaladas en el venv compartido. Para reinstalarlas:

```powershell
.\Precalculo\venv\Scripts\python.exe -m pip install -r .\Dash\requirements.txt
```

Los resultados derivados se entregan en `data/`. Si cambian notebook o CSV fuente:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
```

La preparación reproduce el pipeline del notebook y verifica sus métricas. No modifica fuentes.
El dashboard comprueba hashes al iniciar y rechaza caché desactualizada.
Guarda el pipeline en `data/model.joblib`, con hash verificado antes de cargarlo.
Reproduce la alternativa 2 únicamente para el contraste de aumentación, sobre los
originales ya preservados de train: no repite el split ni utiliza test. Comprueba
sus métricas frente al notebook y guarda `data/augmentation.csv.gz`.

## Lectura de resultados

- EDA, modelos y dashboard usan exclusivamente los CSV de `Precalculo/comparacion_aumentacion/`, generados con la alternativa 1 seleccionada: perturbación local.
- Los notebooks se reejecutaron sobre esta fuente: 24.000 filas de train y 6.000 de test, sin incumplimientos. Los CSV anteriores se conservan como históricos.
- Métricas, intervalos, diagnósticos y curva de aprendizaje provienen de `Precalculo/resultados/` y se actualizan al ejecutar `Precalculo/actualizar_analisis.py`.
- Validación global: media de cinco folds. Validación filtrada: métricas agrupadas OOF.
- Los filtros evalúan el modelo global; no entrenan modelos independientes.
- El test evaluado contiene variantes sintéticas y no equivale al test original de 301 filas recomendado para futuras evaluaciones.

Consultar `CONTEXT.md` para decisiones, cifras y limitaciones. Mantenerlo actualizado en cada modificación según `AGENTS.md`.

Verificación desde la raíz:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
```

Nueve pruebas validan correspondencia con el notebook, integridad, filtros,
callbacks HTTP, recursos locales, contraste de aumentación, reporte de β y predicción.

Para actualizar todo el análisis después de modificar la generación seleccionada:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Precalculo\actualizar_analisis.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
```

Después, actualizar ambos documentos de contexto y reiniciar el servidor.

Referencias técnicas: [callbacks de Dash](https://dash.plotly.com/basic-callbacks) y [pestañas de Dash](https://dash.plotly.com/dash-core-components/tabs).
