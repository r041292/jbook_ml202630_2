# Opciones de regresión mejorada para E3

Fecha de búsqueda: 2026-10-14. Criterio confirmado: se acepta código de referencia
pero se excluye una librería Python con el modelo listo para usar. Se revisaron
artículos originales, repositorios de autores y resultados de búsqueda de paquetes.
No identificar un paquete no demuestra inexistencia universal; repetir la comprobación
al elegir el modelo. Usar NumPy/SciPy o PyTorch como componentes no equivale a
usar una librería que ya implementa el algoritmo completo.

Referencia local: 1.309 filas train, 1.293 estudiantes, 15 predictoras mixtas;
XGBoost RMSE externo 0.8143/test 0.9063. Ninguna alternativa tiene garantizada
una mejora en esta muestra o en el periodo posterior. Las prioridades son juicios
de encaje e implementación, no resultados de una evaluación local.

| Opción | Mejora propuesta | Software revisado | Encaje |
| --- | --- | --- | --- |
| MOB con regresión lineal | Detectar heterogeneidad de parámetros y ajustar regresiones por regiones. | Implementación de referencia en R/partykit; no se identificó Python listo para el MOB exacto. | Alto, interpretable; requiere limitar tamaño/profundidad de regiones. |
| logicDT con regresión en hojas / bagging | Buscar interacciones booleanas explícitas y efectos continuos locales. | Paquete oficial R/CRAN; no se identificó librería Python lista. | Alto para categorías; esfuerzo medio-alto. |
| GBT por clusters de K-means o bisecting K-means | Expertos locales asignados por proximidad al centroide. | Paper con implementación personalizada PySpark; no se identificó estimador empaquetado del procedimiento completo. | Alto como extensión práctica; grupos pequeños limitan estabilidad. |
| SparseLinTab | Atención dispersa entre filas y columnas. | Repositorio experimental Python; no se identificó distribución lista del modelo. | Experimental; costo y control de contexto/transducción. |
| TabResFlow | Modelar distribución condicional con flujo spline y ResNet. | Repositorio de investigación PyTorch; no se identificó librería lista del modelo completo. | Secundario para incertidumbre; NLL no equivale a mejora de RMSE. |

## Evidencia y matices

- MOB: marco de partición por inestabilidad de parámetros, distinto de simplemente
  ajustar Ridge en hojas de un CART. Su fundamento no garantiza vencer XGBoost.
  Fuentes: [paper original](https://www.zeileis.org/papers/Zeileis%2BHothorn%2BHornik-2008.pdf),
  [partykit/JMLR](https://www.jmlr.org/papers/v16/hothorn15a.html).
- logicDT: el teorema de consistencia cubre el núcleo de predictores binarios y
  búsqueda por simulated annealing bajo sus supuestos. No trasladarlo automáticamente
  a una variante greedy regularizada con múltiples covariables continuas.
  Fuentes: [paper](https://link.springer.com/article/10.1007/s10994-023-06488-6),
  [manual oficial](https://michlau.r-universe.dev/logicDT/doc/manual.html).
- GBT por clusters: evidencia en 40 datasets frente a un GBT global. Usar XGBoost
  como experto sería una adaptación. Elegir K en CV interna; el protocolo descrito
  en el paper no equivale a nuestra CV agrupada y evaluación temporal.
  Fuente: [Rizkallah, 2025](https://link.springer.com/article/10.1186/s40537-025-01071-3).
- SparseLinTab: evidencia mixta en siete datasets, solo dos tareas de regresión;
  no usar la media entre métricas de clasificación/regresión como prueba de
  superioridad. Auditar etiquetas y separación de estudiantes en atención entre filas.
  Fuentes: [paper publicado en 2026](https://www.sciencedirect.com/science/article/pii/S2667295225000832),
  [código de referencia](https://github.com/linlin227295/SparseLinTab).
- TabResFlow: sus mejoras principales son probabilísticas, sobre likelihood/NLL.
  No justifican por sí solas prometer menor RMSE que nuestro XGBoost.
  Fuentes: [paper](https://arxiv.org/abs/2508.17056),
  [código oficial](https://github.com/18kiran12/TabResFlow).

## Descartes por disponibilidad

- RaFFLE/PILOT: [fast-model-trees en PyPI](https://pypi.org/project/fast-model-trees/).
- GUIDE: [pyguide](https://github.com/bgreenwell/pyguide), API lista de árboles y ensembles.
- TabR/TabM: [pytabkit](https://github.com/dholzmueller/pytabkit).
- MSBoost: [repo](https://github.com/Agnij-Moitra/MSBoost) contiene setup.py y módulo
  Cython; descarte conservador por estar estructurado como extensión instalable.
- Q-aggregation: existe variante causal empaquetada en
  [metacausal](https://pypi.org/project/metacausal/); no se presenta como opción
  inequívocamente libre de librerías, aunque difiere de la agregación de regresión original.
- APAR: [paper](https://arxiv.org/abs/2412.10941) usa regularización con aumentación;
  no es primera elección para el flujo solicitado sin aumentación.

## Prioridad propuesta y evaluación

Empezar por MOB para heterogeneidad interpretable y/o por GBT-clusters para una
extensión directa del predictor actual. logicDT es atractivo si el aporte principal
es estudiar interacciones y fundamentos teóricos. SparseLinTab/TabResFlow son
experimentos secundarios, no mejoras aseguradas.

Conservar los cinco folds externos por estudiante. Ajustar selección de variables,
clustering, términos, early stopping e hiperparámetros exclusivamente dentro del
train externo y CV interna. No usar ID ni periodo como predictores. No crear datos
sintéticos ni alterar los registros reales. Respetar la exclusión de nota_final.
Separar consistencia asintótica, complejidad computacional y mejora empírica finita.
La adaptación de un algoritmo debe nombrarse como adaptación si modifica sus
reglas o supuestos, en vez de atribuirle automáticamente los teoremas originales.
