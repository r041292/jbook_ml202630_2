:::{table} Dashboard: pares de finalistas del MCS de 15 modelos (contraste por estudiante con HLN).
:label: tab-her-finalistas

| Modelo A | Modelo B | Δ RMSE (A − B) | IC 95 % Δ RMSE | p crudo | p HLN | Conclusión |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kernel Ridge RBF | GPR–XGBoost (OOF agrupado) | −0,0019 | [−0,0055; 0,0018] | 0,3244 | 0,3247 | Diferencia no significativa |
| Kernel Ridge RBF | Truncated Newton KRR RBF | −0,0047 | [−0,0118; 0,0012] | 0,1622 | 0,1626 | Diferencia no significativa |
| Kernel Ridge RBF | SVR RBF | −0,0065 | [−0,0134; 0,0004] | 0,0649 | 0,0653 | Diferencia no significativa |
| GPR–XGBoost (OOF agrupado) | Truncated Newton KRR RBF | −0,0029 | [−0,0121; 0,0051] | 0,5165 | 0,5167 | Diferencia no significativa |
| GPR–XGBoost (OOF agrupado) | SVR RBF | −0,0046 | [−0,0127; 0,0034] | 0,2632 | 0,2636 | Diferencia no significativa |
| Truncated Newton KRR RBF | SVR RBF | −0,0018 | [−0,0090; 0,0053] | 0,6297 | 0,6299 | Diferencia no significativa |
:::
