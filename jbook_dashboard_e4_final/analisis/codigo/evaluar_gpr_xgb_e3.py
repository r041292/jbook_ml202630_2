"""GPR–XGBoost apilado para E3, con validación agrupada y test temporal final."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import permutation_test
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, RBF, WhiteKernel
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from entregable3 import (
    BOOK, OUTPUT, FEATURES, GROUP, PERIOD, TARGET, load_partitions,
    make_pipeline, metrics, source_hashes, grouped_splits, write_json,
)

KEY = "gpr_xgb"
LABEL = "GPR–XGBoost (OOF agrupado)"
PAPER_URL = "https://arxiv.org/abs/2610.15862"
OUTER_FOLDS = 5
INNER_FOLDS = 5
GPR_RESTARTS = 1
SEED = 42
OUTPUT_DIR = OUTPUT / KEY

# Parámetros XGBoost reportados en el artículo. Se limita el número de hojas
# para adaptar el árbol al N pequeño y a las variables one-hot de E3.
XGB_PARAMS = {
    "n_estimators": 1000,
    "learning_rate": 0.01,
    "max_depth": 0,
    "grow_policy": "lossguide",
    "max_leaves": 31,
    "tree_method": "hist",
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 1.0,
    "reg_lambda": 1.0,
    "objective": "reg:squarederror",
    "random_state": SEED,
    "n_jobs": 4,
    "verbosity": 0,
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def partitions():
    """Usa los pliegues externos canónicos ya guardados para E3."""
    train, test, audit = load_partitions()
    baseline = json.loads((OUTPUT / "modelos_lineales.json").read_text(encoding="utf-8"))
    if baseline.get("source_sha256") != source_hashes():
        raise ValueError("La fuente E3 cambió respecto de las particiones canónicas.")
    for frame, name in ((train, "train"), (test, "test")):
        saved = pd.read_csv(OUTPUT / f"{name}.csv.gz")
        pd.testing.assert_frame_equal(
            frame[FEATURES + [TARGET, PERIOD]],
            saved[FEATURES + [TARGET, PERIOD]],
            check_dtype=False, check_exact=False, rtol=1e-12,
        )
    assignments = pd.read_csv(OUTPUT / "train.csv.gz")["fold"].to_numpy(dtype=int)
    if len(assignments) != len(train) or set(np.unique(assignments)) != set(range(1, OUTER_FOLDS + 1)):
        raise ValueError("Los folds canónicos de entrenamiento están incompletos.")
    folds = []
    for fold in range(1, OUTER_FOLDS + 1):
        valid_idx = np.flatnonzero(assignments == fold)
        fit_idx = np.flatnonzero(assignments != fold)
        if not len(valid_idx) or set(train.iloc[fit_idx][GROUP]) & set(train.iloc[valid_idx][GROUP]):
            raise ValueError(f"Fold externo {fold} mezcla estudiantes o no tiene validación.")
        folds.append((fit_idx, valid_idx))
    if set(train[GROUP]) & set(test[GROUP]):
        raise ValueError("Hay estudiantes compartidos entre train y el test temporal.")
    return train, test, folds, audit


def _preprocessor():
    # Reutiliza imputación, log1p, escalado y one-hot del pipeline canónico E3.
    return clone(make_pipeline().named_steps["preprocesamiento"])


def _dense(values):
    if hasattr(values, "toarray"):
        values = values.toarray()
    return np.asarray(values, dtype=np.float64)


def _new_gpr():
    kernel = (
        ConstantKernel(1.0, (1e-3, 1e3))
        * (
            Matern(length_scale=1.0, length_scale_bounds=(1e-2, 1e2), nu=2.5)
            + RBF(length_scale=0.5, length_scale_bounds=(1e-2, 1e2))
        )
        + WhiteKernel(noise_level=1e-2, noise_level_bounds=(1e-5, 1e1))
    )
    return GaussianProcessRegressor(
        kernel=kernel,
        alpha=1e-8,
        normalize_y=True,
        n_restarts_optimizer=GPR_RESTARTS,
        random_state=SEED,
        copy_X_train=False,
    )


def _fit_gpr_predict(fit_frame, y_fit, predict_frame):
    prep = _preprocessor()
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        warnings.filterwarnings("ignore", message="Found unknown categories")
        z_fit = _dense(prep.fit_transform(fit_frame[FEATURES]))
        z_pred = _dense(prep.transform(predict_frame[FEATURES]))
        model = _new_gpr().fit(z_fit, np.asarray(y_fit, dtype=float))
        mean, std = model.predict(z_pred, return_std=True)
    mean, std = np.asarray(mean, float), np.asarray(std, float)
    if not np.isfinite(mean).all() or not np.isfinite(std).all() or (std < 0).any():
        raise ValueError("GPR produjo medias o incertidumbres inválidas.")
    return mean, std, str(model.kernel_)


def crossfit_gpr(frame, fold_label):
    """Genera media/desviación OOF; cada predicción excluye al estudiante."""
    mean_oof = np.full(len(frame), np.nan, dtype=float)
    std_oof = np.full(len(frame), np.nan, dtype=float)
    audits = []
    splits = grouped_splits(frame, n_splits=INNER_FOLDS)
    for inner, (fit_idx, valid_idx) in enumerate(splits, 1):
        fit_frame, valid_frame = frame.iloc[fit_idx], frame.iloc[valid_idx]
        if set(fit_frame[GROUP]) & set(valid_frame[GROUP]):
            raise ValueError("Un fold interno GPR comparte estudiantes entre ajuste y validación.")
        started = time.perf_counter()
        print(
            f"GPR-XGBoost: {fold_label}, GPR interno {inner}/{INNER_FOLDS}; "
            f"fit={len(fit_idx)}, validación={len(valid_idx)}",
            flush=True,
        )
        mean, std, kernel = _fit_gpr_predict(
            fit_frame, fit_frame[TARGET].to_numpy(float), valid_frame
        )
        mean_oof[valid_idx] = mean
        std_oof[valid_idx] = std
        audits.append({
            "inner_fold": inner,
            "fit_rows": len(fit_idx),
            "validation_rows": len(valid_idx),
            "shared_students": 0,
            "kernel_optimized": kernel,
            "seconds": time.perf_counter() - started,
        })
        del mean, std
        gc.collect()
    if not np.isfinite(mean_oof).all() or not np.isfinite(std_oof).all():
        raise ValueError("Las meta-features OOF de GPR están incompletas.")
    return mean_oof, std_oof, audits


def _new_xgb():
    return XGBRegressor(**XGB_PARAMS)


def fit_hybrid_predict(fit_frame, predict_frame, label):
    """Ajusta el stack GPR→XGB con residuos y meta-features sin leakage."""
    y_fit = fit_frame[TARGET].to_numpy(float)
    started = time.perf_counter()
    gp_mean_oof, gp_std_oof, inner_audit = crossfit_gpr(fit_frame, label)

    # La transformación del meta-modelo se ajusta solo en el fit externo.
    xgb_prep = _preprocessor()
    z_fit = _dense(xgb_prep.fit_transform(fit_frame[FEATURES]))
    z_predict = _dense(xgb_prep.transform(predict_frame[FEATURES]))

    # La predicción externa usa un GPR reentrenado en todo el fit externo.
    gp_mean_predict, gp_std_predict, final_kernel = _fit_gpr_predict(
        fit_frame, y_fit, predict_frame
    )
    xgb_fit = np.column_stack([z_fit, gp_mean_oof, gp_std_oof])
    xgb_predict = np.column_stack([z_predict, gp_mean_predict, gp_std_predict])
    residual = y_fit - gp_mean_oof
    xgb = _new_xgb().fit(xgb_fit, residual)
    prediction = gp_mean_predict + xgb.predict(xgb_predict)
    if not np.isfinite(prediction).all():
        raise ValueError("GPR-XGBoost produjo predicciones inválidas.")
    audit = {
        "seconds": time.perf_counter() - started,
        "fit_rows": len(fit_frame),
        "predict_rows": len(predict_frame),
        "input_features_after_encoding": int(z_fit.shape[1]),
        "stack_features": int(xgb_fit.shape[1]),
        "gpr_kernel_full_fit": final_kernel,
        "gpr_inner_folds": inner_audit,
        "xgb_params": XGB_PARAMS,
    }
    return np.asarray(prediction, float), gp_mean_predict, audit


def _validate_classic_baseline():
    report_path = OUTPUT / "clasicos" / "comparacion.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    paths = [
        "modelos_clasicos.py",
        "preprocesamiento_clasicos.py",
        "resultados/e3/modelos_lineales.json",
        "resultados/e3/train.csv.gz",
        "resultados/e3/test.csv.gz",
        "resultados/e3/fold_metrics.csv",
    ]
    expected = {
        **source_hashes(),
        **{path: sha256(BOOK / path) for path in paths},
    }
    if report.get("source_sha256") != expected:
        raise ValueError("XGBoost guardado no corresponde a las particiones E3 actuales.")
    predictions = pd.read_csv(OUTPUT / "clasicos" / "test_predictions.csv.gz")
    if "xgboost" not in predictions:
        raise ValueError("No se encontró la predicción clásica XGBoost.")
    return predictions["xgboost"].to_numpy(float)


def reference_predictions(test):
    """Carga referencias guardadas y alinea cada archivo con test 202530."""
    refs = {"SVM lineal": pd.read_csv(OUTPUT / "test.csv.gz")["svm"].to_numpy(float)}
    refs["XGBoost"] = _validate_classic_baseline()
    paths = {
        "TabICLv2": OUTPUT / "tabicl_v2" / "test_predictions.csv.gz",
        "TabPFN 2.5 original": OUTPUT / "tabpfn_25" / "test_predictions.csv.gz",
        "TabFM 1.0.0 (PyTorch CPU, 32 vistas)": OUTPUT / "tabfm" / "test_predictions.csv.gz",
        "TCR-XGBoost": OUTPUT / "tcr_xgboost" / "test_predictions.csv.gz",
        "Kernel Ridge RBF": OUTPUT / "scopus" / "kernel_ridge" / "test_predictions.csv.gz",
        "CatBoost": OUTPUT / "scopus" / "catboost" / "test_predictions.csv.gz",
    }
    fine_tuned = sorted((OUTPUT / "tabpfn_25_finetuned").glob("*/test_predictions.csv.gz"))
    if len(fine_tuned) != 1:
        raise ValueError("Se esperaba una ejecución fine-tuned de TabPFN para comparar.")
    paths["TabPFN 2.5 fine-tuned"] = fine_tuned[0]

    for name, path in paths.items():
        frame = pd.read_csv(path)
        if len(frame) != len(test) or "prediccion" not in frame:
            raise ValueError(f"Predicciones de referencia incompletas: {name}.")
        for column in (TARGET, PERIOD):
            if column not in frame or not np.array_equal(frame[column], test[column]):
                raise ValueError(f"El archivo de {name} no está alineado con test 202530.")
        if "fila_fuente" in frame and not np.array_equal(frame["fila_fuente"], test["fila_fuente"]):
            raise ValueError(f"fila_fuente no coincide para {name}.")
        refs[name] = frame["prediccion"].to_numpy(float)

    for name, values in refs.items():
        if values.shape != (len(test),) or not np.isfinite(values).all():
            raise ValueError(f"Predicciones inválidas en la referencia {name}.")
    return refs, paths, fine_tuned[0]


def provenance(fine_tuned_path):
    input_paths = [
        "evaluacion_nuevos_e3.py",
        "resultados/e3/train.csv.gz",
        "resultados/e3/test.csv.gz",
        "resultados/e3/modelos_lineales.json",
        "resultados/e3/fold_metrics.csv",
        "resultados/e3/resumen_completo/modelos.csv",
        "resultados/e3/scopus/contrastes_pareados.csv",
        "resultados/e3/clasicos/comparacion.json",
        "resultados/e3/clasicos/test_predictions.csv.gz",
        "resultados/e3/tabicl_v2/test_predictions.csv.gz",
        "resultados/e3/tabpfn_25/test_predictions.csv.gz",
        "resultados/e3/tabfm/reporte.json",
        "resultados/e3/tabfm/test_predictions.csv.gz",
        "resultados/e3/tcr_xgboost/test_predictions.csv.gz",
        "resultados/e3/scopus/kernel_ridge/test_predictions.csv.gz",
        "resultados/e3/scopus/catboost/test_predictions.csv.gz",
    ]
    package_versions = {
        name: importlib.metadata.version(name)
        for name in ["numpy", "pandas", "scikit-learn", "scipy", "statsmodels", "xgboost"]
    }
    return {
        **source_hashes(),
        "evaluar_gpr_xgb_e3.py": sha256(BOOK / "evaluar_gpr_xgb_e3.py"),
        "experiment_inputs_sha256": {path: sha256(BOOK / path) for path in input_paths},
        "tabpfn_finetuned_predictions_sha256": sha256(fine_tuned_path),
        "versions": package_versions,
        "paper": PAPER_URL,
        "configuration": {
            "outer_folds": OUTER_FOLDS,
            "inner_gpr_group_folds": INNER_FOLDS,
            "gpr_kernel": "Constant*(Matern(nu=2.5)+RBF)+White",
            "gpr_lml_restarts": GPR_RESTARTS,
            "gpr_normalize_y": True,
            "xgboost": XGB_PARAMS,
            "features": "pipeline E3: imputación, log1p/escala numérica y one-hot categórico",
            "test_period": 202530,
            "conformal": "95%; score máximo por estudiante sobre residuo OOF agrupado",
        },
    }


def paired_comparison(y, new, old, groups, seed=SEED):
    """Permutación y bootstrap por estudiante; la estadística principal es SSE."""
    codes, ids = pd.factorize(groups, sort=False)
    aggregate = lambda values: np.bincount(codes, weights=values, minlength=len(ids))
    new_sse = aggregate((y - new) ** 2)
    old_sse = aggregate((y - old) ** 2)
    test_result = permutation_test(
        (new_sse - old_sse,),
        lambda values, axis: values.sum(axis=axis),
        permutation_type="samples",
        vectorized=True,
        n_resamples=99999,
        batch=512,
        alternative="two-sided",
        rng=np.random.default_rng(seed),
    )

    n = aggregate(np.ones(len(y)))
    sum_y = aggregate(y)
    sum_y2 = aggregate(y * y)
    rng = np.random.default_rng(seed)
    rmse_delta, r2_delta = [], []
    for start in range(0, 10000, 512):
        batch = min(512, 10000 - start)
        idx = rng.integers(len(ids), size=(batch, len(ids)))
        count = n[idx].sum(axis=1)
        sse_new, sse_old = new_sse[idx].sum(axis=1), old_sse[idx].sum(axis=1)
        sst = sum_y2[idx].sum(axis=1) - sum_y[idx].sum(axis=1) ** 2 / count
        if (sst <= 0).any():
            raise ValueError("Varianza nula en el bootstrap por estudiante.")
        rmse_delta.extend(np.sqrt(sse_new / count) - np.sqrt(sse_old / count))
        r2_delta.extend((sse_old - sse_new) / sst)

    new_metrics, old_metrics = metrics(y, new), metrics(y, old)
    rmse_ci = np.quantile(rmse_delta, [0.025, 0.975])
    r2_ci = np.quantile(r2_delta, [0.025, 0.975])
    return [
        {
            "metrica": "RMSE",
            "diferencia_GPR_XGB_menos_referencia": new_metrics["RMSE"] - old_metrics["RMSE"],
            "IC_2.5%": float(rmse_ci[0]),
            "IC_97.5%": float(rmse_ci[1]),
            "p_bilateral": float(test_result.pvalue),
        },
        {
            "metrica": "R²",
            "diferencia_GPR_XGB_menos_referencia": new_metrics["R²"] - old_metrics["R²"],
            "IC_2.5%": float(r2_ci[0]),
            "IC_97.5%": float(r2_ci[1]),
            "p_bilateral": float(test_result.pvalue),
        },
        {
            "metrica": "MAE",
            "diferencia_GPR_XGB_menos_referencia": new_metrics["MAE"] - old_metrics["MAE"],
            "p_bilateral": None,
        },
        {
            "metrica": "MAPE (%)",
            "diferencia_GPR_XGB_menos_referencia": new_metrics["MAPE (%)"] - old_metrics["MAPE (%)"],
            "p_bilateral": None,
        },
    ]


def _write_progress(rows, audits, signature):
    write_json(OUTPUT_DIR / "progreso.json", {
        "folds": rows,
        "audit": audits,
        "provenance": signature,
    })


def conformal_radius(train, oof):
    """Cuantil split-conformal finito con score máximo absoluto por estudiante."""
    absolute_error = np.abs(train[TARGET].to_numpy(float) - oof)
    scores = pd.DataFrame({GROUP: train[GROUP].to_numpy(), "score": absolute_error})
    group_scores = scores.groupby(GROUP, sort=False)["score"].max().to_numpy(float)
    n_groups = len(group_scores)
    rank = min(n_groups, math.ceil((n_groups + 1) * 0.95))
    radius = float(np.sort(group_scores)[rank - 1])
    return radius, n_groups, rank


def run(force=False):
    train, test, folds, partition_audit = partitions()
    fine_files = sorted((OUTPUT / "tabpfn_25_finetuned").glob("*/test_predictions.csv.gz"))
    if len(fine_files) != 1:
        raise ValueError("Se esperaba una sola predicción TabPFN fine-tuned.")
    signature = provenance(fine_files[0])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "reporte.json"
    if report_path.is_file() and not force:
        cached = json.loads(report_path.read_text(encoding="utf-8"))
        if cached.get("provenance") == signature:
            print("GPR-XGBoost: resultados completos y procedencia coincidente; usa --force para repetir.", flush=True)
            return cached

    oof = np.full(len(train), np.nan, dtype=float)
    oof_gpr = np.full(len(train), np.nan, dtype=float)
    fold_rows, fold_audits = [], []
    for fold, (fit_idx, valid_idx) in enumerate(folds, 1):
        checkpoint_path = OUTPUT_DIR / f"externo_{fold}.json"
        pred_path = OUTPUT_DIR / f"oof_{fold}.csv.gz"
        if checkpoint_path.is_file() and pred_path.is_file() and not force:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint.get("provenance") == signature:
                saved = pd.read_csv(pred_path)
                expected = train.iloc[valid_idx]
                if (len(saved) != len(valid_idx)
                        or not np.array_equal(saved["fila_fuente"], expected["fila_fuente"])
                        or not np.array_equal(saved["fold"], np.full(len(valid_idx), fold))
                        or "gpr_solo_prediccion" not in saved
                        or "gpr_solo_metrics" not in checkpoint.get("audit", {})):
                    raise ValueError(f"Checkpoint OOF del fold {fold} no coincide con el split canónico.")
                oof[valid_idx] = saved["prediccion"].to_numpy(float)
                oof_gpr[valid_idx] = saved["gpr_solo_prediccion"].to_numpy(float)
                fold_rows.append(checkpoint["metrics"])
                fold_audits.append(checkpoint["audit"])
                print(f"GPR-XGBoost: fold {fold}/{OUTER_FOLDS} reutilizado.", flush=True)
                continue

        fit_frame, valid_frame = train.iloc[fit_idx], train.iloc[valid_idx]
        print(
            f"GPR-XGBoost: fold externo {fold}/{OUTER_FOLDS}; "
            f"fit={len(fit_idx)}, validación={len(valid_idx)}",
            flush=True,
        )
        prediction, gpr_prediction, audit = fit_hybrid_predict(
            fit_frame, valid_frame, f"fold externo {fold}"
        )
        oof[valid_idx] = prediction
        oof_gpr[valid_idx] = gpr_prediction
        metric_row = {"Modelo": LABEL, "Fold": fold, **metrics(valid_frame[TARGET], prediction)}
        gpr_metric_row = {
            "Modelo": "GPR solo",
            "Fold": fold,
            **metrics(valid_frame[TARGET], gpr_prediction),
        }
        audit.update({
            "fold": fold,
            "fit_students": int(fit_frame[GROUP].nunique()),
            "validation_students": int(valid_frame[GROUP].nunique()),
            "shared_students": int(len(set(fit_frame[GROUP]) & set(valid_frame[GROUP]))),
            "gpr_solo_metrics": gpr_metric_row,
        })
        export = valid_frame[["fila_fuente", PERIOD, TARGET]].copy()
        export["fold"] = fold
        export["prediccion"] = prediction
        export["gpr_solo_prediccion"] = gpr_prediction
        export["residuo"] = export[TARGET] - prediction
        export.to_csv(pred_path, index=False, compression="gzip")
        write_json(checkpoint_path, {
            "metrics": metric_row,
            "audit": audit,
            "provenance": signature,
        })
        fold_rows.append(metric_row)
        fold_audits.append(audit)
        _write_progress(fold_rows, fold_audits, signature)
        pd.DataFrame(fold_rows).sort_values("Fold").to_csv(
            OUTPUT_DIR / "fold_metrics.csv", index=False, encoding="utf-8-sig"
        )
        print(
            f"GPR-XGBoost: fold {fold} RMSE={metric_row['RMSE']:.6f}; "
            f"GPR sola={gpr_metric_row['RMSE']:.6f}.",
            flush=True,
        )
        gc.collect()

    if not np.isfinite(oof).all() or not np.isfinite(oof_gpr).all():
        raise ValueError("Predicciones OOF incompletas.")
    fold_frame = pd.DataFrame(fold_rows).sort_values("Fold")
    fold_frame.to_csv(OUTPUT_DIR / "fold_metrics.csv", index=False, encoding="utf-8-sig")
    train_export = train[["fila_fuente", PERIOD, TARGET]].copy()
    train_export["fold"] = pd.read_csv(OUTPUT / "train.csv.gz")["fold"].to_numpy(dtype=int)
    train_export["prediccion"] = oof
    train_export["gpr_solo_prediccion"] = oof_gpr
    train_export["residuo"] = train_export[TARGET] - oof
    train_export["residuo_gpr_solo"] = train_export[TARGET] - oof_gpr
    train_export.to_csv(OUTPUT_DIR / "train_predictions.csv.gz", index=False, compression="gzip")
    gpr_fold_frame = pd.DataFrame(
        [audit["gpr_solo_metrics"] for audit in fold_audits]
    ).sort_values("Fold")
    gpr_fold_frame.to_csv(
        OUTPUT_DIR / "fold_metrics_gpr_solo.csv", index=False, encoding="utf-8-sig"
    )

    radius, calibration_groups, calibration_rank = conformal_radius(train, oof)
    write_json(OUTPUT_DIR / "seleccion_antes_test.json", {
        "paper": PAPER_URL,
        "test_used": False,
        "selection": "Kernel GPR y parámetros XGBoost fijos del artículo/adaptación; sin HPO E3",
        "xgboost_parameters": XGB_PARAMS,
        "gpr_restarts": GPR_RESTARTS,
        "conformal_radius_95": radius,
        "conformal_calibration_students": calibration_groups,
        "conformal_order_statistic": calibration_rank,
        "cv_outer_rmse_mean": float(fold_frame["RMSE"].mean()),
    })

    print("GPR-XGBoost: cinco folds completos; inicio del ajuste final y test 202530.", flush=True)
    test_prediction, test_gpr_prediction, final_audit = fit_hybrid_predict(
        train, test, "ajuste final"
    )
    test_score = metrics(test[TARGET], test_prediction)
    gpr_test_score = metrics(test[TARGET], test_gpr_prediction)
    lower = test_prediction - radius
    upper = test_prediction + radius
    test_export = test[["fila_fuente", PERIOD, TARGET]].copy()
    test_export["prediccion"] = test_prediction
    test_export["gpr_solo_prediccion"] = test_gpr_prediction
    test_export["residuo"] = test_export[TARGET] - test_prediction
    test_export["residuo_gpr_solo"] = test_export[TARGET] - test_gpr_prediction
    test_export["limite_inferior_95"] = lower
    test_export["limite_superior_95"] = upper
    test_export.to_csv(OUTPUT_DIR / "test_predictions.csv.gz", index=False, compression="gzip")
    interval_coverage = float(((test[TARGET].to_numpy(float) >= lower)
                               & (test[TARGET].to_numpy(float) <= upper)).mean())

    refs, _, _ = reference_predictions(test)
    refs["GPR solo"] = test_gpr_prediction
    y = test[TARGET].to_numpy(float)
    comparisons = []
    for name, old_prediction in refs.items():
        comparisons.append({
            "referencia": name,
            "rows": paired_comparison(y, test_prediction, old_prediction, test[GROUP]),
        })

    # Familia predeclarada E3: 17 métodos vs SVM, 4 previos vs XGBoost,
    # 2 TabFM y 10 contrastes nuevos, incluida la ablación GPR sola.
    previous = pd.read_csv(OUTPUT / "resumen_completo" / "modelos.csv")
    previous_svm_p = previous["p_bilateral"].dropna().to_numpy(float)
    prior_scopus = pd.read_csv(OUTPUT / "scopus" / "contrastes_pareados.csv")
    prior_xgb_p = prior_scopus.loc[
        prior_scopus["Referencia"].eq("XGBoost") & prior_scopus["metrica"].eq("RMSE"),
        "p_bilateral",
    ].to_numpy(float)
    tabfm_report = json.loads((OUTPUT / "tabfm" / "reporte.json").read_text(encoding="utf-8"))
    tabfm_p = [
        comparison["rows"][0]["p_bilateral"]
        for comparison in tabfm_report["paired_comparisons"]
    ]
    current_p = np.asarray([comparison["rows"][0]["p_bilateral"] for comparison in comparisons])
    if (len(previous_svm_p) != 17 or len(prior_xgb_p) != 4
            or len(tabfm_p) != 2 or len(current_p) != 10):
        raise ValueError("La familia predeclarada de contrastes E3 no tiene 33 hipótesis.")
    holm_vs_svm = multipletests(
        np.r_[previous_svm_p, tabfm_p[0], current_p[0]], method="holm"
    )[1]
    holm_global = multipletests(
        np.r_[previous_svm_p, prior_xgb_p, tabfm_p, current_p], method="holm"
    )[1]
    for comparison, adjusted in zip(comparisons, holm_global[-len(comparisons):]):
        comparison["p_Holm_global_33"] = float(adjusted)
        for metric_row in comparison["rows"]:
            if metric_row.get("p_bilateral") is not None:
                metric_row["p_Holm_global_33"] = float(adjusted)
                metric_row["significativa_al_5%_Holm"] = bool(adjusted < 0.05)
    comparisons[0]["p_Holm_19_vs_SVM"] = float(holm_vs_svm[-1])

    pd.DataFrame([
        {"referencia": comparison["referencia"], **row}
        for comparison in comparisons for row in comparison["rows"]
    ]).to_csv(OUTPUT_DIR / "contrastes_pareados.csv", index=False, encoding="utf-8-sig")

    ranking = previous[["Modelo", "RMSE_test"]].copy()
    ranking = pd.concat([ranking, pd.DataFrame([
        {"Modelo": tabfm_report["model"], "RMSE_test": tabfm_report["test"]["RMSE"]},
        {"Modelo": LABEL, "RMSE_test": test_score["RMSE"]},
    ])], ignore_index=True)
    svm_rmse = metrics(y, refs["SVM lineal"])["RMSE"]
    ranking["delta_RMSE_vs_SVM"] = ranking["RMSE_test"] - svm_rmse
    ranking["p_Holm_19_vs_SVM"] = np.nan
    ranking.loc[ranking["Modelo"].ne("SVM lineal"), "p_Holm_19_vs_SVM"] = holm_vs_svm
    ranking = ranking.sort_values("RMSE_test").reset_index(drop=True)
    ranking.insert(0, "rango_RMSE", np.arange(1, len(ranking) + 1))
    ranking.to_csv(OUTPUT_DIR / "ranking_rmse_test.csv", index=False, encoding="utf-8-sig")

    report = {
        "model": LABEL,
        "key": KEY,
        "paper": PAPER_URL,
        "test": test_score,
        "cv": [
            {"metrica": metric, "media_cv": float(fold_frame[metric].mean()),
             "sd_cv": float(fold_frame[metric].std(ddof=0)),
             "OOF_agrupado": metrics(train[TARGET], oof)[metric]}
            for metric in test_score
        ],
        "gpr_solo": {
            "test": gpr_test_score,
            "cv": [
                {"metrica": metric,
                 "media_cv": float(gpr_fold_frame[metric].mean()),
                 "sd_cv": float(gpr_fold_frame[metric].std(ddof=0)),
                 "OOF_agrupado": metrics(train[TARGET], oof_gpr)[metric]}
                for metric in gpr_test_score
            ],
        },
        "conformal_95": {
            "radius": radius,
            "calibration_students": calibration_groups,
            "order_statistic": calibration_rank,
            "test_coverage_descriptive": interval_coverage,
            "test_mean_width": float(np.mean(upper - lower)),
            "score": "máximo absoluto de residuos OOF por estudiante",
        },
        "fold_audit": fold_audits,
        "final_fit_audit": final_audit,
        "partition": partition_audit,
        "provenance": signature,
        "features": FEATURES,
        "target": TARGET,
        "paired_comparisons": comparisons,
        "family_size_vs_svm": 19,
        "family_size_global": 33,
        "test_used_for_selection": False,
        "method": (
            "GPR exacto con OOF GroupKFold de 5 por estudiante; XGBoost aprende "
            "y-yhat_GPR con variables E3 codificadas, media y desviación GPR; "
            "mismos folds externos E3; test temporal al final."
        ),
        "adaptations": [
            "Variables mixtas E3: imputación, log1p y escalado numérico, one-hot categórico.",
            "XGBoost usa max_depth=0/lossguide y max_leaves=31 para contener complejidad con N pequeño.",
            "Validación agrupada por estudiante y test temporal, frente a la partición aleatoria del artículo.",
            "Conformal agrupado usa el máximo residuo absoluto OOF por estudiante.",
        ],
        "limitations": [
            "El preprint evalúa 582 datos de ingeniería con división aleatoria 80/20; sus métricas no predicen E3.",
            "El test temporal ya fue consultado en experimentos anteriores; la inferencia es exploratoria.",
            "La cobertura conformal en 202530 es descriptiva ante posible cambio temporal.",
            "GPR exacto y cross-fitting pueden ser lentos; el progreso queda guardado por fold externo.",
            "Parámetros XGBoost fijos del artículo/adaptación; no hay HPO específico para E3.",
        ],
    }
    write_json(report_path, report)

    summary = [
        "# GPR–XGBoost en E3",
        "",
        "Adaptación del stack GPR→XGBoost de arXiv:2610.15862. GPR genera media e incertidumbre; XGBoost aprende residuos con esas señales y las variables E3.",
        "GPR out-of-fold por estudiante; cinco folds externos canónicos; hiperparámetros fijos antes de evaluar el test temporal.",
        "",
        "## Métricas",
        "",
        "| Métrica | Media 5 folds | SD | OOF agrupado | Test 202530 |",
        "|---|---:|---:|---:|---:|",
    ]
    cv_by_metric = {item["metrica"]: item for item in report["cv"]}
    for metric in test_score:
        item = cv_by_metric[metric]
        summary.append(
            f"| {metric} | {item['media_cv']:.6f} | {item['sd_cv']:.6f} | "
            f"{item['OOF_agrupado']:.6f} | {test_score[metric]:.6f} |"
        )
    summary.extend([
        "",
        "## Ablación GPR sola",
        "",
        "| Métrica | Media 5 folds | OOF agrupado | Test 202530 |",
        "|---|---:|---:|---:|",
    ])
    gpr_cv_by_metric = {item["metrica"]: item for item in report["gpr_solo"]["cv"]}
    for metric in gpr_test_score:
        item = gpr_cv_by_metric[metric]
        summary.append(
            f"| {metric} | {item['media_cv']:.6f} | {item['OOF_agrupado']:.6f} | "
            f"{gpr_test_score[metric]:.6f} |"
        )
    summary.extend([
        "",
        f"Intervalo conformal agrupado nominal 95%: radio={radius:.6f}; cobertura observada en test={interval_coverage:.4f} (descriptiva).",
        "",
        "## Contrastes pareados",
        "",
        "Permutación por estudiante: 99.999 reasignaciones; bootstrap: 10.000; semilla 42.",
        "Holm global 33: familia histórica de 23 más diez contrastes contra SVM, XGBoost, TabICLv2, TabPFN original/fine-tuned, TabFM, TCR-XGBoost, Kernel Ridge, CatBoost y GPR solo.",
        "RMSE y R² comparten el contraste SSE; los IC son marginales.",
        "",
        "| Referencia | Δ RMSE | IC95% marginal | p bilateral | p Holm global33 |",
        "|---|---:|---:|---:|---:|",
    ])
    for comparison in comparisons:
        row = comparison["rows"][0]
        summary.append(
            f"| {comparison['referencia']} | {row['diferencia_GPR_XGB_menos_referencia']:+.6f} | "
            f"[{row['IC_2.5%']:+.6f}, {row['IC_97.5%']:+.6f}] | "
            f"{row['p_bilateral']:.5f} | {row['p_Holm_global_33']:.5f} |"
        )
    summary.extend([
        "",
        "La partición aleatoria del preprint y sus resultados de ingeniería no se comparan directamente con E3.",
        "El test temporal ya fue consultado en experimentos anteriores; interpretar los contrastes como exploratorios.",
    ])
    (OUTPUT_DIR / "resumen.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({"test": test_score, "cv": report["cv"], "comparisons": comparisons}, ensure_ascii=False), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recalcula incluso los folds guardados.")
    run(force=parser.parse_args().force)
