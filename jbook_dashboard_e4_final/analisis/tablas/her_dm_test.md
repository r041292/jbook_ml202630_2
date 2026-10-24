:::{table} Dashboard: mismo contraste en el test 202530 (188 estudiantes).
:label: tab-her-dm-test

| Modelo vs SVM | Δ RMSE | IC 95 % Δ RMSE | p crudo | p HLN |
| --- | ---: | ---: | ---: | ---: |
| Kernel Ridge RBF | −0,0208 | [−0,0458; 0,0018] | 0,0927 | 0,0952 |
| GPR–XGBoost (OOF agrupado) | −0,0270 | [−0,0550; −0,0010] | 0,0512 | 0,0534 |
| Truncated Newton KRR RBF | −0,0203 | [−0,0441; 0,0020] | 0,0882 | 0,0908 |
| SVR RBF | −0,0249 | [−0,0485; −0,0049] | 0,0261 | 0,0277 |
| Ridge | −0,0129 | [−0,0345; 0,0037] | 0,1998 | 0,2026 |
:::
