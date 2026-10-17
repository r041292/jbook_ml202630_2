# Diagnóstico previo de stacking — E3

El usuario propone combinar TabICLv2, TabPFN2.5 original, Kernel Ridge RBF y
XGBoost y pregunta si podría mejorar. Se revisaron exclusivamente sus predicciones
OOF existentes de train, verificando orden, objetivos y folds contra los archivos
canónicos. No se entrenó un metamodelo ni se evaluó un stacking en test.

| Método | RMSE OOF reunido en train |
|---|---:|
| TabICLv2 | 0.8082167931 |
| TabPFN2.5 original | 0.8083108784 |
| Kernel Ridge RBF | 0.8022446535 |
| XGBoost | 0.8148217146 |
| Promedio uniforme de los cuatro | 0.8017275396 |
| Promedio uniforme de TabICL y TabPFN | 0.8052950529 |

Estos valores NO son RMSE del test temporal ni media de los RMSE por fold.
Los promedios son diagnósticos descriptivos prefijados, sin pesos aprendidos,
no nuevos modelos incorporados al listado de18 ni evidencia de significancia.

Correlaciones Pearson entre errores OOF (predicción−nota): TabICL/TabPFN.9860;
TabICL/KRR.9861; TabICL/XGB.9708; TabPFN/KRR.9811;
TabPFN/XGB.9744; KRR/XGB.9717. Alta correlación limita la expectativa
de reducción por promediar; no demuestra imposibilidad de mejora.
La media de cuatro baja apenas.0005171139 respecto a KRR en OOF.

Propuesta de experimento: promedio uniforme como control, stacking con Ridge
regularizado y combinación convexa con pesos no negativos que sumen1. Elegir
solo en train. En cada fold externo, generar de nuevo las predicciones internas
del metamodelo mediante GroupKFold dentro del fit externo; ningún componente
puede entrenar con estudiantes de la validación externa. Preparación/HPO de
las bases respeta el fit correspondiente. Evaluar el pipeline completo fuera.
Las OOF globales existentes permiten diagnóstico y entrenamiento del combinador
final, pero no sustituyen una CV independiente del stacking completo: tampoco
evaluar el metamodelo en las mismas filas con las que aprende.

Test202530 solo después de cerrar selección; comparar con SVM y con el mejor
modelo individual, TabICLv2; corregir la familia ampliada de contrastes y mantener
carácter exploratorio por reutilización del test.

[Documentación oficial de StackingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html):
el metamodelo usa predicciones cruzadas y RidgeCV es su opción por defecto.
El default de CV para regresión es KFold; este proyecto requiere splits explícitos
por estudiante. Se evita prefit sobre predicciones de entrenamiento de las bases.
