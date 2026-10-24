:::{table} p ajustado por Holm (familia de 21 por prueba) de cada original frente a cada modelo base. En negrita, p < 0,05; en todas las celdas en negrita la diferencia favorece al original.
:label: tab-matriz-holm

| Original | Prueba | SVM lineal | KNN | Ridge | Lasso | Random Forest | XGBoost | Decision Tree |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KRR centrado | Wilcoxon por fold | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| KRR centrado | Permutación pareada por estudiante | **0,0040** | **0,0021** | **0,0030** | **0,0021** | **0,0021** | **0,0312** | **0,0021** |
| KRR centrado | t corregida de Nadeau–Bengio | 1,0000 | 0,1421 | 1,0000 | 1,0000 | 0,6341 | 1,0000 | **0,0111** |
| KRR centrado | Bootstrap pareado BCa | **< 0,0001** | **0,0019** | **< 0,0001** | **< 0,0001** | **0,0019** | **0,0221** | **0,0019** |
| KRR centrado | Diebold–Mariano por estudiante (HLN) | **0,0181** | **< 0,0001** | 0,0519 | **0,0261** | **0,0005** | 0,0519 | **< 0,0001** |
| TN-KRR | Wilcoxon por fold | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| TN-KRR | Permutación pareada por estudiante | **0,0030** | **0,0021** | **0,0022** | **0,0021** | **0,0180** | 0,1469 | **0,0021** |
| TN-KRR | t corregida de Nadeau–Bengio | 1,0000 | 0,3456 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | **0,0391** |
| TN-KRR | Bootstrap pareado BCa | **0,0008** | **0,0019** | **< 0,0001** | **< 0,0001** | **0,0221** | 0,1748 | **0,0019** |
| TN-KRR | Diebold–Mariano por estudiante (HLN) | **0,0041** | **< 0,0001** | **0,0194** | **0,0056** | **0,0283** | 0,1520 | **< 0,0001** |
| GPR–XGBoost | Wilcoxon por fold | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| GPR–XGBoost | Permutación pareada por estudiante | **0,0240** | **0,0021** | **0,0312** | **0,0105** | **0,0021** | **0,0312** | **0,0021** |
| GPR–XGBoost | t corregida de Nadeau–Bengio | 1,0000 | 0,2013 | 1,0000 | 1,0000 | 0,7844 | 1,0000 | **0,0175** |
| GPR–XGBoost | Bootstrap pareado BCa | **0,0024** | **0,0019** | **0,0008** | **< 0,0001** | **0,0024** | **0,0221** | **0,0019** |
| GPR–XGBoost | Diebold–Mariano por estudiante (HLN) | 0,0519 | **< 0,0001** | 0,0519 | 0,0519 | **0,0005** | 0,0519 | **< 0,0001** |
:::
