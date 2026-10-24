"""Lee atributos de los pipelines finales ya ajustados (sin `fit` ni `predict`).

Registra el diagnóstico del solver TN-KRR (iteraciones, norma residual, motivo de parada),
la media de centrado del KRR y el kernel optimizado del GPR del híbrido, desde los `.joblib`
de la ejecución activa de Originales. Salida: `salidas/diagnostico_modelos.json`.
"""
import json

import joblib

from comun import OUT, RUN_ORIG


def main():
    krr = joblib.load(RUN_ORIG / 'm5.joblib').named_steps['modelo']
    tn = joblib.load(RUN_ORIG / 'm19.joblib').named_steps['modelo']
    stack = joblib.load(RUN_ORIG / 'm15.joblib').named_steps['modelo']
    report = {
        'KRR centrado (m5)': {'alpha': krr.regressor_.alpha, 'gamma': krr.regressor_.gamma,
                              'media_de_centrado_y': float(krr.transformer_.mean_[0]),
                              'n_entrenamiento': int(krr.regressor_.X_fit_.shape[0]),
                              'columnas_transformadas': int(krr.regressor_.X_fit_.shape[1])},
        'TN-KRR (m19)': {'alpha': tn.alpha, 'gamma': tn.gamma, 'iteraciones_cg': int(tn.n_iter_),
                         'norma_residual_final': float(tn.residual_norm_), 'convergio': bool(tn.converged_),
                         'motivo_de_parada': tn.stop_reason_, 'max_iter': tn.max_iter,
                         'tolerancia': tn.cg_tolerance, 'max_sin_mejora': tn.max_no_improve,
                         'n_entrenamiento': int(tn.X_fit_.shape[0]), 'columnas_transformadas': int(tn.X_fit_.shape[1])},
        'GPR–XGBoost (m15)': {'kernel_gpr_optimizado': str(stack.gpr_.kernel_),
                              'xgboost': {k: getattr(stack, k) for k in ('n_estimators', 'learning_rate', 'max_leaves', 'reg_lambda',
                                                                        'subsample', 'colsample_bytree', 'reg_alpha', 'random_state')},
                              'entradas_xgboost': int(stack.xgb_.n_features_in_)},
    }
    (OUT / 'diagnostico_modelos.json').write_text(json.dumps(report, ensure_ascii=False, indent=1, default=float), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=1, default=float))


if __name__ == '__main__':
    main()
