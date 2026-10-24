:::{table} Dashboard: contraste tipo Diebold–Mariano por estudiante frente al SVM (CV, 1.293 estudiantes).
:label: tab-her-dm-cv

| Modelo vs SVM | Posición MCS | Δ MSE | Δ RMSE | IC 95 % Δ RMSE | p crudo | p HLN | p t corregida |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kernel Ridge RBF | 1 | −0,0380 | −0,0234 | [−0,0384; −0,0099] | 0,0016 | 0,0016 | 0,2466 |
| GPR–XGBoost (OOF agrupado) | 2 | −0,0351 | −0,0215 | [−0,0384; −0,0062] | 0,0095 | 0,0096 | 0,3349 |
| Truncated Newton KRR RBF | 3 | −0,0304 | −0,0187 | [−0,0287; −0,0087] | 0,0003 | 0,0003 | 0,1937 |
| SVR RBF | 4 | −0,0276 | −0,0169 | [−0,0297; −0,0047] | 0,0090 | 0,0092 | 0,3768 |
| Ridge | 5 | 0,0022 | 0,0014 | [−0,0064; 0,0096] | 0,7488 | 0,7490 | 0,7807 |
:::
