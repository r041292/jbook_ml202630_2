:::{table} Extracto de la tabla maestra: filas de procedimiento anidado (métricas del bucle externo).
:label: tab-maestra-extracto

| Grupo | Modelo | RMSE externo | MAE externo | R² externo | RMSE test | Semilla | Ejecución activa |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Original del proyecto | KRR centrado | 0,8010 ± 0,0419 | 0,6300 ± 0,0367 | 0,4832 | 0,9091 | 42 | `nan` |
| Original del proyecto | GPR–XGBoost | 0,8028 ± 0,0429 | 0,6296 ± 0,0391 | 0,4807 | 0,9029 | 42 | `nan` |
| Original del proyecto | TN-KRR | 0,8056 ± 0,0453 | 0,6335 ± 0,0383 | 0,4774 | 0,9096 | 42 | `nan` |
| Complementario (pestaña Originales) | SVR RBF | 0,8075 ± 0,0418 | 0,6302 ± 0,0405 | 0,4743 | 0,9050 | 42 | `nan` |
| Complementario (pestaña Originales) | DenseWeight-XGB | 0,8143 ± 0,0406 | 0,6434 ± 0,0333 | 0,4658 | 0,9087 | 42 | `nan` |
| Base (benchmark) | XGBoost | 0,8156 ± 0,0344 | 0,6447 ± 0,0264 | 0,4646 | 0,9137 | 42 | `20261018_102325_af643f83` |
| Complementario (pestaña Originales) | TCR-XGBoost | 0,8157 ± 0,0343 | 0,6446 ± 0,0266 | 0,4644 | 0,9089 | 42 | `nan` |
| Base (benchmark) | SVM lineal | 0,8241 ± 0,0479 | 0,6503 ± 0,0408 | 0,4530 | 0,9299 | 42 | `20261018_102325_af643f83` |
| Base (benchmark) | Ridge | 0,8253 ± 0,0520 | 0,6514 ± 0,0399 | 0,4514 | 0,9170 | 42 | `20261018_102325_af643f83` |
| Base (benchmark) | Lasso | 0,8288 ± 0,0561 | 0,6542 ± 0,0439 | 0,4465 | 0,9197 | 42 | `20261018_102325_af643f83` |
| Base (benchmark) | Random Forest | 0,8297 ± 0,0294 | 0,6619 ± 0,0291 | 0,4457 | 0,9396 | 42 | `20261018_102325_af643f83` |
| Complementario (pestaña Originales) | logicDT adaptado | 0,8451 ± 0,0605 | 0,6677 ± 0,0401 | 0,4231 | 0,9689 | 42 | `nan` |
| Complementario (pestaña Originales) | LinXGBoost | 0,8457 ± 0,0565 | 0,6679 ± 0,0502 | 0,4230 | 0,9152 | 42 | `nan` |
| Base (benchmark) | KNN | 0,8550 ± 0,0400 | 0,6809 ± 0,0308 | 0,4121 | 0,9239 | 42 | `20261018_102325_af643f83` |
| Complementario (pestaña Originales) | RIM | 0,8646 ± 0,0276 | 0,6715 ± 0,0333 | 0,3981 | 0,9883 | 42 | `nan` |
| Base (benchmark) | Decision Tree | 0,8948 ± 0,0325 | 0,7123 ± 0,0335 | 0,3552 | 1,0104 | 42 | `20261018_102325_af643f83` |
:::
