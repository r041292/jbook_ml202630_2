# Originales: actualización de búsquedas, comparación e interpretabilidad

Ejecución local activa: `20261019_083039_147f9845`. Se preservan las ejecuciones
anteriores en `historico/` y el código exacto de la ejecución en `evidencia/`.
CSV brutos y notebooks anteriores permanecen intactos.

Se completaron cinco estrategias (Grid, Random, TPE, DEAP y Successive Halving)
para SVR RBF, Kernel Ridge RBF y TR-KRR. Cada entrenamiento externo selecciona
método y parámetros con cinco folds internos por estudiante; el ajuste final
repite la selección en todo train. Solo compiten finalistas a fidelidad completa.
Todos los parámetros se cierran antes de inferir test. SVM, KNN, Ridge, Lasso,
Random Forest y XGBoost reutilizan la ejecución multibúsqueda clásica vigente.

Se realizaron 90 búsquedas (3 modelos × 6 entrenamientos × 5 estrategias),
2.004 ensayos de configuración/fidelidad y 10.020 fits internos: cero fallos,
cero grupos compartidos y particiones idénticas entre estrategias a igual
fidelidad. Presupuesto: Random16, TPE20/inicio6/EI24, DEAP población8 y tres
generaciones/élite1/torneo3/cruce0.8/intercambio0.5/mutación0.3 por individuo y
1/d por gen, SH16→8→4 con 25/50/100% de grupos. Cuatro procesos internos,
un hilo por proceso. Grid histórico35 se conserva para KRR/TR-KRR; SVR tenía
Random histórico, por lo que se declara una nueva rejilla27 antes de ejecutar.
Los dominios y presupuestos difieren entre estrategias, no es una comparación
de eficiencia uniforme. No se selecciona por tiempo.

Líder descriptivo por RMSE medio CV: **Kernel Ridge RBF, 0.8009641043621**.
No significa superioridad estadística confirmada. La comparación mantiene los
estados «actualizado», «reutilizado», «histórico» y «configuración fija» explícitos.

## Comparación estadística

- Etapa1: Friedman sobre25modelos con cinco folds completos; se excluyen Dummy
  y TabPFN fine-tuned, que no tiene OOF independiente. χ²70.4344615/gl24/
  p1.87872e-6. Interpretación exploratoria por solapamiento y solo cinco bloques.
- Etapa2: MCS T_R/e_R con3125remuestreos emparejados de folds,alfa0.10;
  sin cobertura90% garantizada. Retiene KRR,TR-KRR,SVR,TabFM yTabPFN original.
- Etapa3:25comparaciones contra SVM del test,188estudiantes. Bootstrap-t
  bilateral centrado bajoH0,49.999réplicas/semilla20261018,Holm25;ICBCa95
  individuales con jackknife por estudiante. No hay diferencias con pHolm<0.05;
  no demuestra equivalencia. No usa Friedman como puerta de un contraste test.

Los p históricos se archivan y no se aplican a las predicciones nuevas.
No hay GW/CW,DM-HLN o bootstrap estacionario artificial: no hay una secuencia
de pronóstico/horizonte/anidamiento justificadas. Test ya inspeccionado:
inferencia exploratoria condicionada a modelos fijos y periodo202530,asumiendo
independencia entre estudiantes,sin variación de entrenamiento ni otros periodos.

## SHAP y LIME: solo el líder CV

SHAP aproximado mediante permutaciones antitéticas sobre las15variables
originales del pipeline completo. Todas las1497filas válidas se explican;
referencia empírica32filas de train,64caminos,semilla42,predict por lotes256.
No es TreeSHAP ni permutation feature importance. La suma base+aportes reproduce
la predicción,pero eso no vuelve exacta la estimación de Shapley. Diferencia
media absoluta entre dos mitades de referencias0.04546puntos: diagnóstico de
sensibilidad,no IC ni garantía de convergencia. Las coaliciones pueden romper
correlaciones/avance;no son causas ni intervenciones factibles.

Ejemplos test0072(menor error) y0118(mayor). LIME empírico1000filas del train
con regresión Ridge local para esos mismos casos. Se distinguen el error del
modelo frente a la nota y la brecha del sustituto frente al modelo. Caso0072:
R²local≈0.798 y brecha≈0.728puntos;un buen R²del vecindario no garantiza que
LIME coincida con esa predicción. Los selectores de otros modelos no cambian
la interpretabilidad del líder. Los filtros solo agregan/visualizan valores
ya guardados, sin nuevas inferencias.

Referencias: [SHAP por permutaciones](https://shap.readthedocs.io/en/stable/generated/shap.PermutationExplainer.html),
[SHAP](https://arxiv.org/abs/1705.07874), [LIME](https://arxiv.org/abs/1602.04938).

## Pendientes autorizados para revisión, sin ejecutar

| Modelo | Candidatos de la rejilla preparada | Revisión necesaria |
|---|---:|---|
| LinXGBoost | 2880 | Presupuesto Grid y coste de hojas lineales |
| CatBoost | 24 | Coste de las cinco estrategias |
| TCR-XGBoost | 10 | Rejilla condicional/control y ponderación |
| XGBoost ampliado | 103680 | Reducir/redefinir resolución Grid antes de autorizar ejecución |
| RaFFLE | 12 | Coste de bosques PILOT |
| DenseWeight-XGBoost | 622080 | Presupuesto Grid y densidad ajustada solo en fit |
| DART-XGBoost | 7464960 | Presupuesto Grid; dropout y tiempo de inferencia |
| HRT-Boost | 12 | Coste de árboles con hojas lineales |
| logicDT adaptado | 16 | Recocido, reinicios y coste |
| RIM | 8 | Épocas, recuperación y grupos en cada fit |
| XBART GFR | 8 | Coste del muestreo GFR |
| coPILOT | 18 | Coste de árboles lineales |

Las factorías y dominios están construidos sin entrenar. Más de1000candidatos
requiere `--allow-large-grid`; **no se recomienda activar ese permiso sin
revisar antes la rejilla**. Los grids de distribuciones continuas pendientes
usan tres anclas declaradas por dimensión; no pretenden ser grids históricos.
Cambiar resolución/presupuesto define un protocolo nuevo que debe fijarse
antes de ejecutar. Modelos preentrenados/fijos (TabICL,TabPFN,TabFM,GPR–XGB)
y el fine-tuning de TabPFN conservan sus protocolos; no se simulan cinco búsquedas
que nunca se hicieron.

## Reproducción local

Usar solo `Precalculo/venv/Scripts/python.exe` desde la raíz:

```powershell
Precalculo/venv/Scripts/python.exe -X utf8 Precalculo/evaluar_originales_busquedas_e3.py
Precalculo/venv/Scripts/python.exe -X utf8 Dash/activate_originals.py Precalculo/resultados/e3/originales_busquedas/<run_id_completo>
Precalculo/venv/Scripts/python.exe -X utf8 Dash/run_measured.py --tests
```

Para un modelo costoso, tras revisar su presupuesto, usar `--models m6`, etc.
Los identificadores y comandos están en `pendientes.json`. RIM recibe grupos
tanto en fitness como en refit; no se mezclan estudiantes en recuperación interna.
Toda búsqueda/refit/inferencia se mide antes de ejecutar. Los tiempos de
fit/predict internos están en ensayos por fold,incluidos dentro de la búsqueda;
no sumarlos con el tiempo de pared. Total del experimento383.6865575s;
SHAP+LIME61.5331041s en una ejecución separada,no incluido en el anterior.
Registros completos y fallos: `TIEMPOS_EJECUCION.md` y `tiempos/`.

La activación comprueba predicciones/folds y hashes,copia solo artefactos sinIDs
al dashboard y actualiza su manifiesto. La ejecución parcial/nueva no modifica
el tablero hasta activación. Cambios actuales locales,sin push ni despliegue.
