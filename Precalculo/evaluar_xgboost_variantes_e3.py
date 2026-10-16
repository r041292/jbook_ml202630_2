"""Compara XGBoost-DART y DenseWeight-XGBoost con GroupKFold anidado E3.

Incluye XGBoost gbtree con búsqueda ampliada como control metodológico. Cada
variante se selecciona solo con train; el test temporal 202530 se usa al final.
Los predictores, reglas de negocio y folds son los canónicos de Entregable 3.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import loguniform, uniform
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from entregable3 import (
    BOOK,
    FEATURES,
    GROUP,
    OUTPUT as E3_OUTPUT,
    PERIOD,
    TARGET,
    grouped_splits,
    metrics,
    source_hashes,
    write_json,
)
from modelos_clasicos import classic_pipeline
import evaluar_svr_rbf_raffle_e3 as e3_comparison


KEY = "xgboost_variantes"
LABELS = {
    "gbtree": "XGBoost ampliado (gbtree)",
    "dart": "DART-XGBoost",
    "denseweight": "DenseWeight-XGBoost",
}
KEYS = tuple(LABELS)
SEED = 42
OUTER_FOLDS = 5
INNER_FOLDS = 5
SEARCH_ITERATIONS = 20
N_JOBS = 4
OUTPUT_DIR = E3_OUTPUT / KEY
PRIVATE_DIR = BOOK / "modelos_preentrenados" / KEY
WEIGHT_EPSILON = 1e-3
_DENSE_WEIGHT_CACHE: dict[str, np.ndarray] = {}

BASE_DISTRIBUTIONS = {
    "modelo__n_estimators": [150, 250, 400, 600],
    "modelo__max_depth": [1, 2, 3, 4],
    "modelo__learning_rate": loguniform(0.01, 0.15),
    "modelo__min_child_weight": [1, 3, 5, 8],
    "modelo__subsample": [0.6, 0.8, 1.0],
    "modelo__colsample_bytree": [0.6, 0.8, 1.0],
    "modelo__gamma": [0.0, 0.05, 0.1, 0.3],
    "modelo__reg_lambda": loguniform(0.1, 20.0),
    "modelo__reg_alpha": [0.0, 0.001, 0.01, 0.1, 1.0],
}
DART_PARAM_DISTRIBUTIONS = {
    **BASE_DISTRIBUTIONS,
    "modelo__rate_drop": uniform(0.02, 0.38),
    "modelo__skip_drop": uniform(0.0, 0.3),
    "modelo__sample_type": ["uniform", "weighted"],
    "modelo__normalize_type": ["tree", "forest"],
    "modelo__one_drop": [0, 1],
}
DENSEWEIGHT_PARAM_DISTRIBUTIONS = {
    **BASE_DISTRIBUTIONS,
    "modelo__weight_alpha": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25],
}


def sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def denseweight_sample_weights(y, alpha: float, epsilon: float = WEIGHT_EPSILON):
    """KDE-based DenseWeight adaptation, computed only from the current fit y."""
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    if len(y) < 3 or not np.isfinite(y).all():
        raise ValueError("DenseWeight necesita al menos tres objetivos finitos.")
    cache_key = hashlib.sha256(
        np.asarray([float(alpha), float(epsilon)], dtype=np.float64).tobytes() + y.tobytes()
    ).hexdigest()
    if cache_key in _DENSE_WEIGHT_CACHE:
        return _DENSE_WEIGHT_CACHE[cache_key].copy()

    standard_deviation = float(np.std(y, ddof=1))
    if standard_deviation <= 0:
        result = np.ones(len(y), dtype=np.float64)
        _DENSE_WEIGHT_CACHE[cache_key] = result
        return result.copy()

    q25, q75 = np.quantile(y, [0.25, 0.75])
    robust_scale = float((q75 - q25) / 1.34)
    scale = min(standard_deviation, robust_scale) if robust_scale > 0 else standard_deviation
    bandwidth = 0.9 * scale * len(y) ** (-0.2)
    if not np.isfinite(bandwidth) or bandwidth <= 1e-8:
        bandwidth = 1.06 * standard_deviation * len(y) ** (-0.2)

    distances = (y[:, None] - y[None, :]) / bandwidth
    density = np.exp(-0.5 * distances * distances).mean(axis=1)
    density_range = float(np.ptp(density))
    normalized_density = (
        (density - density.min()) / density_range
        if density_range > 1e-12
        else np.ones_like(density)
    )
    raw = np.maximum(1.0 - float(alpha) * normalized_density, epsilon)
    result = raw / raw.mean()
    _DENSE_WEIGHT_CACHE[cache_key] = result
    return result.copy()


class DenseWeightXGBRegressor(RegressorMixin, BaseEstimator):
    """XGBoost regressor using fold-local density-based target weights."""

    def __init__(
        self,
        weight_alpha=0.5,
        n_estimators=300,
        max_depth=2,
        learning_rate=0.03,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=0.0,
        reg_lambda=3.0,
        reg_alpha=0.0,
        random_state=SEED,
    ):
        self.weight_alpha = weight_alpha
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.min_child_weight = min_child_weight
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.gamma = gamma
        self.reg_lambda = reg_lambda
        self.reg_alpha = reg_alpha
        self.random_state = random_state

    def fit(self, X, y):
        y = np.asarray(y, dtype=np.float64).reshape(-1)
        weights = denseweight_sample_weights(y, self.weight_alpha)
        self.model_ = XGBRegressor(
            objective="reg:squarederror",
            tree_method="hist",
            enable_categorical=True,
            max_cat_to_onehot=1,
            booster="gbtree",
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            min_child_weight=self.min_child_weight,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            gamma=self.gamma,
            reg_lambda=self.reg_lambda,
            reg_alpha=self.reg_alpha,
            random_state=self.random_state,
            n_jobs=1,
            verbosity=0,
        )
        self.model_.fit(X, y, sample_weight=weights)
        self.n_features_in_ = X.shape[1]
        self.sample_weight_summary_ = {
            "alpha": float(self.weight_alpha),
            "min": float(weights.min()),
            "median": float(np.median(weights)),
            "max": float(weights.max()),
            "mean": float(weights.mean()),
        }
        return self

    def predict(self, X):
        return self.model_.predict(X)


def _base_xgb(booster="gbtree"):
    return XGBRegressor(
        objective="reg:squarederror",
        tree_method="hist",
        enable_categorical=True,
        max_cat_to_onehot=1,
        booster=booster,
        n_estimators=300,
        max_depth=2,
        learning_rate=0.03,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=3.0,
        reg_alpha=0.0,
        random_state=SEED,
        n_jobs=1,
        verbosity=0,
    )


def _pipeline(key: str):
    preprocessing = clone(classic_pipeline("xgboost").named_steps["preprocesamiento"])
    if key == "gbtree":
        model = _base_xgb("gbtree")
    elif key == "dart":
        model = _base_xgb("dart")
    elif key == "denseweight":
        model = DenseWeightXGBRegressor()
    else:
        raise KeyError(key)
    return Pipeline([("preprocesamiento", preprocessing), ("modelo", model)])


def _describe_param_space(space):
    """Representa distribuciones scipy de forma estable para checkpoints."""
    description = {}
    for name, value in space.items():
        if hasattr(value, "dist") and hasattr(value, "args"):
            description[name] = {
                "distribution": value.dist.name,
                "args": [float(item) for item in value.args],
                "kwargs": {key: float(item) for key, item in value.kwds.items()},
            }
        else:
            description[name] = list(value) if isinstance(value, (list, tuple)) else value
    return description


def _provenance_matches(saved: dict, current: dict) -> bool:
    """Allow output/comparison-only edits without invalidating trained folds."""
    saved = json.loads(json.dumps(saved))
    current = json.loads(json.dumps(current))
    for signature in (saved, current):
        signature.get("experiment_inputs_sha256", {}).pop("xgboost_variants_evaluator", None)
    return e3_comparison._checkpoint_provenance_matches(saved, current)


def _read_variant_report(path: Path, signature: dict):
    report = json.loads(path.read_text(encoding="utf-8"))
    if not _provenance_matches(report.get("provenance", {}), signature):
        raise ValueError(
            f"Cambió la procedencia de {path.name}; usa --force para recalcular ese modelo."
        )
    return report


def _configuration():
    return {
        "outer_folds": OUTER_FOLDS,
        "inner_group_folds": INNER_FOLDS,
        "seed": SEED,
        "search": "RandomizedSearchCV; neg_root_mean_squared_error; GroupKFold por estudiante",
        "n_iter_per_variant": SEARCH_ITERATIONS,
        "models": {
            "gbtree": {
                "booster": "gbtree",
                "param_distributions": _describe_param_space(BASE_DISTRIBUTIONS),
            },
            "dart": {
                "booster": "dart",
                "param_distributions": _describe_param_space(DART_PARAM_DISTRIBUTIONS),
            },
            "denseweight": {
                "booster": "gbtree",
                "param_distributions": _describe_param_space(DENSEWEIGHT_PARAM_DISTRIBUTIONS),
                "weighting": "KDE normalizada + max(1 - alpha * density, 1e-3), pesos reescalados a media 1",
                "density_fit_scope": "solo objetivos del fold de entrenamiento actual",
            },
        },
        "preprocessing": "pipeline XGBoost E3 canónico; imputación y categorías nativas se ajustan dentro de cada fit",
        "test_period": 202530,
        "test_used_for_selection": False,
    }


def provenance():
    signature = e3_comparison.provenance()
    signature["experiment_inputs_sha256"]["xgboost_variants_evaluator"] = sha256(__file__)
    signature["versions"]["xgboost"] = importlib.metadata.version("xgboost")
    signature["configuration"]["xgboost_variantes"] = _configuration()
    return signature


def _new_search(key: str, fit_frame: pd.DataFrame):
    distributions = {
        "gbtree": BASE_DISTRIBUTIONS,
        "dart": DART_PARAM_DISTRIBUTIONS,
        "denseweight": DENSEWEIGHT_PARAM_DISTRIBUTIONS,
    }[key]
    search = RandomizedSearchCV(
        estimator=_pipeline(key),
        param_distributions=distributions,
        n_iter=SEARCH_ITERATIONS,
        scoring="neg_root_mean_squared_error",
        cv=grouped_splits(fit_frame, n_splits=INNER_FOLDS),
        refit=True,
        n_jobs=N_JOBS,
        random_state=SEED,
        error_score="raise",
        return_train_score=False,
        verbose=1,
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Found unknown categories")
        with threadpool_limits(limits=1):
            with joblib.parallel_backend("loky", inner_max_num_threads=1):
                search.fit(fit_frame[FEATURES], fit_frame[TARGET].to_numpy(float))
    return search


def _search_table(search):
    frame = pd.DataFrame(search.cv_results_)
    return frame[["params", "mean_test_score", "std_test_score", "rank_test_score", "mean_fit_time", "std_fit_time"]].sort_values("rank_test_score")


def _model_directory(key: str):
    return OUTPUT_DIR / key


def _private_directory(key: str):
    return PRIVATE_DIR / key


def run_model(key, signature, train, test, fold_ids, folds, partition_audit, force=False):
    folder = _model_directory(key)
    private = _private_directory(key)
    folder.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    report_path = folder / "reporte.json"
    progress_path = folder / "progreso.json"

    if report_path.is_file() and not force:
        report = _read_variant_report(report_path, signature)
        print(f"{LABELS[key]}: reporte válido existente; se reutiliza.", flush=True)
        return report
    if progress_path.is_file() and not force:
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if not _provenance_matches(progress.get("provenance", {}), signature):
            raise ValueError(f"Cambió la procedencia de {LABELS[key]}; usa --force para reiniciar este modelo.")

    oof = np.full(len(train), np.nan, dtype=float)
    fold_rows, fold_audits = [], []
    for fold, (fit_idx, valid_idx) in enumerate(folds, 1):
        checkpoint_path = folder / f"externo_{fold}.json"
        pred_path = folder / f"oof_{fold}.npy"
        if not force and checkpoint_path.is_file() and pred_path.is_file():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            pred = np.load(pred_path)
            if (
                _provenance_matches(checkpoint.get("provenance", {}), signature)
                and pred.shape == (len(valid_idx),)
                and np.isfinite(pred).all()
            ):
                oof[valid_idx] = pred
                fold_rows.append(checkpoint["metrics"])
                fold_audits.append(checkpoint["audit"])
                print(f"{LABELS[key]}: fold {fold}/5 recuperado del checkpoint.", flush=True)
                continue
            raise ValueError(f"Checkpoint externo {fold} de {LABELS[key]} inválido; usa --force.")

        fit_frame, valid_frame = train.iloc[fit_idx], train.iloc[valid_idx]
        if set(fit_frame[GROUP]) & set(valid_frame[GROUP]):
            raise ValueError(f"El fold {fold} mezcla estudiantes.")
        started = time.perf_counter()
        print(
            f"{LABELS[key]}: fold externo {fold}/5, ajuste={len(fit_idx)}, validación={len(valid_idx)}; HPO anidado.",
            flush=True,
        )
        search = _new_search(key, fit_frame)
        prediction = np.asarray(search.best_estimator_.predict(valid_frame[FEATURES]), dtype=float)
        if prediction.shape != (len(valid_idx),) or not np.isfinite(prediction).all():
            raise ValueError(f"Predicciones inválidas en {LABELS[key]}, fold {fold}.")
        oof[valid_idx] = prediction
        metric_row = {"Modelo": LABELS[key], "Fold": fold, **metrics(valid_frame[TARGET], prediction)}
        audit = {
            "fold": fold,
            "fit_rows": len(fit_idx),
            "validation_rows": len(valid_idx),
            "fit_students": int(fit_frame[GROUP].nunique()),
            "validation_students": int(valid_frame[GROUP].nunique()),
            "shared_students": 0,
            "best_params": search.best_params_,
            "inner_rmse": float(-search.best_score_),
            "seconds": float(time.perf_counter() - started),
        }
        _search_table(search).to_csv(folder / f"busqueda_externa_{fold}.csv", index=False)
        np.save(pred_path, prediction)
        write_json(checkpoint_path, {"metrics": metric_row, "audit": audit, "provenance": signature})
        fold_rows.append(metric_row)
        fold_audits.append(audit)
        write_json(progress_path, {
            "completed_folds": [row["Fold"] for row in fold_rows],
            "fold_metrics": fold_rows,
            "fold_audit": fold_audits,
            "provenance": signature,
        })
        print(f"{LABELS[key]}: fold {fold} RMSE={metric_row['RMSE']:.6f}; {audit['seconds']:.1f}s; {search.best_params_}", flush=True)
        del search
        gc.collect()

    if not np.isfinite(oof).all():
        raise ValueError(f"Predicciones OOF incompletas para {LABELS[key]}.")
    fold_frame = pd.DataFrame(fold_rows).sort_values("Fold")
    fold_frame.to_csv(folder / "fold_metrics.csv", index=False, encoding="utf-8-sig")

    print(f"{LABELS[key]}: HPO final en todo train; test aún no evaluado.", flush=True)
    final_progress = json.loads(progress_path.read_text(encoding="utf-8"))
    selection_path = folder / "seleccion_antes_test.json"
    saved_selection = None
    if (
        selection_path.is_file()
        and set(final_progress.get("completed_folds", [])) == set(range(1, OUTER_FOLDS + 1))
        and _provenance_matches(final_progress.get("provenance", {}), signature)
    ):
        candidate = json.loads(selection_path.read_text(encoding="utf-8"))
        if (
            candidate.get("configuration") == signature["configuration"]["xgboost_variantes"]["models"][key]
            and candidate.get("test_used") is False
            and isinstance(candidate.get("best_params"), dict)
            and _provenance_matches(candidate.get("provenance", {}), signature)
        ):
            saved_selection = candidate

    final_search = None
    if saved_selection is not None:
        final_estimator = _pipeline(key).set_params(**saved_selection["best_params"])
        with threadpool_limits(limits=1):
            final_estimator.fit(train[FEATURES], train[TARGET].to_numpy(float))
        best_params = saved_selection["best_params"]
        inner_rmse = float(saved_selection["inner_rmse"])
        print(f"{LABELS[key]}: selección final recuperada; reajuste con todo train.", flush=True)
    else:
        final_search = _new_search(key, train)
        final_estimator = final_search.best_estimator_
        best_params = final_search.best_params_
        inner_rmse = float(-final_search.best_score_)
        _search_table(final_search).to_csv(folder / "busqueda_final.csv", index=False)

    final_selection = {
        "best_params": best_params,
        "inner_rmse": inner_rmse,
        "configuration": signature["configuration"]["xgboost_variantes"]["models"][key],
        "test_used": False,
        "fold_source": "resultados/e3/train.csv.gz, folds externos canónicos de E3",
        "provenance": signature,
    }
    write_json(selection_path, final_selection)
    model_path = private / "modelo_final.joblib"
    temp_path = private / "modelo_final.joblib.tmp"
    try:
        joblib.dump(final_estimator, temp_path)
        temp_path.replace(model_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    test_prediction = np.asarray(final_estimator.predict(test[FEATURES]), dtype=float)
    if test_prediction.shape != (len(test),) or not np.isfinite(test_prediction).all():
        raise ValueError(f"Predicciones test inválidas para {LABELS[key]}.")
    test_scores = metrics(test[TARGET], test_prediction)
    train_export = train[["fila_fuente", PERIOD, TARGET]].copy()
    train_export["fold"] = fold_ids
    train_export["prediccion"] = oof
    train_export["residuo"] = train_export[TARGET] - oof
    train_export.to_csv(folder / "train_predictions.csv.gz", index=False, compression="gzip")
    test_export = test[["fila_fuente", PERIOD, TARGET]].copy()
    test_export["prediccion"] = test_prediction
    test_export["residuo"] = test_export[TARGET] - test_prediction
    test_export.to_csv(folder / "test_predictions.csv.gz", index=False, compression="gzip")

    report = {
        "model": LABELS[key],
        "key": key,
        "test": test_scores,
        "cv": [
            {
                "metrica": metric,
                "media_cv": float(fold_frame[metric].mean()),
                "sd_cv": float(fold_frame[metric].std(ddof=0)),
                "OOF_agrupado": metrics(train[TARGET], oof)[metric],
            }
            for metric in test_scores
        ],
        "best_params": best_params,
        "inner_rmse": inner_rmse,
        "fold_audit": fold_audits,
        "final_fit_audit": {
            "fit_rows": len(train),
            "fit_students": int(train[GROUP].nunique()),
            "test_rows": len(test),
            "test_students": int(test[GROUP].nunique()),
            "shared_students": 0,
        },
        "partition": partition_audit,
        "provenance": signature,
        "test_used_for_selection": False,
        "method": (
            "Cinco folds externos e cinco internos GroupKFold por estudiante; "
            "búsqueda por RMSE solo en train; test temporal 202530 al final."
        ),
        "limitations": [
            "El test temporal ya se ha consultado en experimentos anteriores; inferencia exploratoria.",
            "DenseWeight es una adaptación del esquema de pesos KDE de la literatura para XGBoost; esa combinación no es la implementación original DenseLoss.",
        ],
    }
    if key == "denseweight":
        report["weighting"] = final_estimator.named_steps["modelo"].sample_weight_summary_
    write_json(report_path, report)
    write_json(progress_path, {
        "completed_folds": list(range(1, OUTER_FOLDS + 1)),
        "fold_metrics": fold_rows,
        "fold_audit": fold_audits,
        "test_complete": True,
        "provenance": signature,
    })
    print(f"{LABELS[key]} TEST: {test_scores}", flush=True)
    del final_estimator
    if final_search is not None:
        del final_search
    gc.collect()
    return report


def _holm_key(name1: str, name2: str):
    return tuple(sorted((name1, name2)))


def _oof_target_band_metrics(train):
    """Descriptive error by fixed grade bands using only out-of-fold predictions."""
    saved_train = pd.read_csv(E3_OUTPUT / "train.csv.gz")
    baseline = pd.read_csv(E3_OUTPUT / "clasicos" / "train_predictions.csv.gz")
    if len(saved_train) != len(train) or len(baseline) != len(train):
        raise ValueError("OOF filas no coinciden con el train canónico.")
    if not np.array_equal(saved_train[TARGET].to_numpy(float), train[TARGET].to_numpy(float)):
        raise ValueError("El objetivo de folds guardados no coincide con train.")
    if not np.array_equal(baseline["fold"].to_numpy(int), saved_train["fold"].to_numpy(int)):
        raise ValueError("Los folds OOF de XGBoost no coinciden con los folds canónicos.")

    predictions = {"XGBoost original": baseline["xgboost"].to_numpy(float)}
    for key in KEYS:
        frame = pd.read_csv(_model_directory(key) / "train_predictions.csv.gz")
        if len(frame) != len(train) or not np.array_equal(frame["fold"].to_numpy(int), saved_train["fold"].to_numpy(int)):
            raise ValueError(f"OOF de {LABELS[key]} no está alineado con los folds canónicos.")
        if not np.array_equal(frame[TARGET].to_numpy(float), train[TARGET].to_numpy(float)):
            raise ValueError(f"Objetivo OOF de {LABELS[key]} no está alineado con train.")
        predictions[LABELS[key]] = frame["prediccion"].to_numpy(float)

    bands = pd.cut(
        train[TARGET].to_numpy(float),
        bins=[0, 1, 2, 3, 4, 5],
        labels=["≤1", "(1,2]", "(2,3]", "(3,4]", ">4"],
        include_lowest=True,
    )
    rows = []
    for model, prediction in predictions.items():
        frame = pd.DataFrame({"y": train[TARGET].to_numpy(float), "prediction": prediction, "band": bands})
        for band, group in frame.groupby("band", observed=False):
            residual = group["y"].to_numpy(float) - group["prediction"].to_numpy(float)
            rows.append({
                "Modelo": model,
                "Tramo_nota": str(band),
                "n": int(len(group)),
                "RMSE_OOF": float(np.sqrt(np.mean(residual * residual))) if len(group) else None,
                "MAE_OOF": float(np.mean(np.abs(residual))) if len(group) else None,
                "sesgo_nota_menos_prediccion": float(np.mean(residual)) if len(group) else None,
            })
    return rows


def compare(train, test, signature):
    reports = {
        key: _read_variant_report(_model_directory(key) / "reporte.json", signature)
        for key in KEYS
    }
    references = e3_comparison.reference_predictions(test)
    svr_rbf_path = e3_comparison._model_directory("svr_rbf") / "test_predictions.csv.gz"
    references["SVR RBF"] = e3_comparison._validate_reference_frame(
        pd.read_csv(svr_rbf_path), "SVR RBF", test
    )
    reference_names = ("XGBoost", "SVR RBF", "TabICLv2")
    y = test[TARGET].to_numpy(float)
    groups = test[GROUP].to_numpy()
    candidate_predictions = {
        key: e3_comparison._validate_reference_frame(
            pd.read_csv(_model_directory(key) / "test_predictions.csv.gz"), LABELS[key], test
        )
        for key in KEYS
    }

    comparisons = []
    p_by_pair = {}
    for key in KEYS:
        for reference in reference_names:
            rows = e3_comparison.paired_comparison(y, candidate_predictions[key], references[reference], groups)
            comparisons.append({"modelo": LABELS[key], "referencia": reference, "rows": rows})
            p_by_pair[_holm_key(LABELS[key], reference)] = rows[0]["p_bilateral"]
    for i, first in enumerate(KEYS):
        for second in KEYS[i + 1:]:
            rows = e3_comparison.paired_comparison(
                y, candidate_predictions[first], candidate_predictions[second], groups
            )
            comparisons.append({"modelo": LABELS[first], "referencia": LABELS[second], "rows": rows})
            p_by_pair[_holm_key(LABELS[first], LABELS[second])] = rows[0]["p_bilateral"]

    p_items = list(p_by_pair.items())
    adjusted = multipletests([p for _, p in p_items], method="holm")[1]
    adjusted_by_pair = {pair: float(value) for (pair, _), value in zip(p_items, adjusted)}
    contrast_rows = []
    for comparison in comparisons:
        pair = _holm_key(comparison["modelo"], comparison["referencia"])
        p_holm = adjusted_by_pair[pair]
        for row in comparison["rows"]:
            row["p_Holm_family_12"] = p_holm if row["p_bilateral"] is not None else None
            row["significativa_al_5%_Holm"] = bool(p_holm < 0.05) if row["p_bilateral"] is not None else False
            contrast_rows.append({
                "Modelo": comparison["modelo"],
                "Referencia": comparison["referencia"],
                **row,
            })
    contrast_frame = pd.DataFrame(contrast_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    contrast_frame.to_csv(OUTPUT_DIR / "contrastes_pareados.csv", index=False, encoding="utf-8-sig")

    baseline_metrics = {
        name: metrics(y, references[name]) for name in reference_names
    }
    ranking_rows = []
    xgb_rmse = baseline_metrics["XGBoost"]["RMSE"]
    for name in reference_names:
        ranking_rows.append({
            "Modelo": name,
            "RMSE_test": baseline_metrics[name]["RMSE"],
            "MAE_test": baseline_metrics[name]["MAE"],
            "MAPE_test": baseline_metrics[name]["MAPE (%)"],
            "R2_test": baseline_metrics[name]["R²"],
            "delta_RMSE_vs_XGBoost": baseline_metrics[name]["RMSE"] - xgb_rmse,
            "p_Holm_family_12": np.nan,
        })
    for key in KEYS:
        score = reports[key]["test"]
        p_holm = adjusted_by_pair[_holm_key(LABELS[key], "XGBoost")]
        ranking_rows.append({
            "Modelo": LABELS[key],
            "RMSE_test": score["RMSE"],
            "MAE_test": score["MAE"],
            "MAPE_test": score["MAPE (%)"],
            "R2_test": score["R²"],
            "delta_RMSE_vs_XGBoost": score["RMSE"] - xgb_rmse,
            "p_Holm_family_12": p_holm,
        })
    candidate_ranking = pd.DataFrame(ranking_rows).sort_values("RMSE_test").reset_index(drop=True)
    candidate_ranking.insert(0, "rango_RMSE", np.arange(1, len(candidate_ranking) + 1))
    candidate_ranking.to_csv(OUTPUT_DIR / "ranking_variantes_y_referencias.csv", index=False, encoding="utf-8-sig")

    previous_ranking = pd.read_csv(e3_comparison.OUTPUT_DIR / "ranking_rmse_test.csv")
    # El CSV histórico ya trae su rango; quitarlo antes de ordenar los 25 modelos
    # y generar el rango consolidado de nuevo.
    previous_ranking = previous_ranking.drop(columns=["rango_RMSE"], errors="ignore")
    previous_ranking["delta_RMSE_vs_XGBoost"] = previous_ranking["RMSE_test"] - xgb_rmse
    previous_ranking["p_bilateral_vs_XGBoost"] = np.nan
    previous_ranking["p_Holm_variantes_12_vs_XGBoost"] = np.nan
    previous_ranking["familia_ajuste"] = "Global E3 anterior (55), contraste de ranking vs SVM"
    new_rows = []
    for key in KEYS:
        score = reports[key]["test"]
        new_rows.append({
            "Modelo": LABELS[key],
            "RMSE_test": score["RMSE"],
            "delta_RMSE_vs_XGBoost": score["RMSE"] - xgb_rmse,
            "p_bilateral_vs_XGBoost": p_by_pair[_holm_key(LABELS[key], "XGBoost")],
            "p_Holm_variantes_12_vs_XGBoost": adjusted_by_pair[_holm_key(LABELS[key], "XGBoost")],
            "familia_ajuste": "Holm 12 contrastes exploratorios de variantes",
        })
    ranking = pd.concat([previous_ranking, pd.DataFrame(new_rows)], ignore_index=True, sort=False)
    ranking = ranking.sort_values("RMSE_test").reset_index(drop=True)
    ranking.insert(0, "rango_RMSE", np.arange(1, len(ranking) + 1))
    ranking.to_csv(OUTPUT_DIR / "ranking_global_25_modelos.csv", index=False, encoding="utf-8-sig")

    oof_bands = _oof_target_band_metrics(train)
    pd.DataFrame(oof_bands).to_csv(OUTPUT_DIR / "oof_por_tramo.csv", index=False, encoding="utf-8-sig")

    for key in KEYS:
        own = reports[key]
        own["paired_comparisons"] = [item for item in comparisons if item["modelo"] == LABELS[key]]
        own["test_used_for_selection"] = False
        write_json(_model_directory(key) / "reporte.json", own)
    aggregate = {
        "models": reports,
        "ranking": ranking.to_dict("records"),
        "ranking_variantes_y_referencias": candidate_ranking.to_dict("records"),
        "contrasts": contrast_frame.to_dict("records"),
        "oof_by_target_band": oof_bands,
        "references": list(reference_names),
        "comparison_reference_sha256": {"SVR RBF test predictions": sha256(svr_rbf_path)},
        "family_size_holm": len(p_items),
        "statistics": (
            "Permutación pareada sobre SSE por estudiante, 99.999 reasignaciones; "
            "bootstrap por estudiante, 10.000 réplicas; semilla 42. RMSE y R² comparten contraste."
        ),
        "test_used_for_selection": False,
        "caveat": "El test temporal ya se ha consultado en rondas previas; los resultados son exploratorios.",
        "provenance": signature,
    }
    write_json(OUTPUT_DIR / "reporte.json", aggregate)
    _write_summary(aggregate, contrast_frame)
    print(ranking.to_string(index=False), flush=True)
    return aggregate


def _write_summary(report, contrasts):
    ranking = pd.DataFrame(report["ranking"])
    candidate_ranking = pd.DataFrame(report["ranking_variantes_y_referencias"])
    rows = contrasts[contrasts["metrica"].eq("RMSE")]
    lines = [
        "# Variantes metodológicas de XGBoost — E3",
        "",
        "Selección anidada 5×5 por GroupKFold de estudiante. El control gbtree amplía la búsqueda",
        "del XGBoost original; DART aplica dropout de árboles; DenseWeight-XGBoost pondera la loss",
        "según la rareza estimada de y dentro de cada fit. Selección solo con train; test 202530 al final.",
        "El test fue consultado en experimentos anteriores, por lo que las comparaciones son exploratorias.",
        "",
        "## Ranking descriptivo por RMSE test: 25 modelos",
        "",
        "| Rango | Modelo | RMSE test | ΔRMSE vs XGBoost |",
        "|---:|---|---:|---:|",
    ]
    for row in ranking.to_dict("records"):
        lines.append(
            f"| {int(row['rango_RMSE'])} | {row['Modelo']} | {row['RMSE_test']:.6f} | "
            f"{row['delta_RMSE_vs_XGBoost']:+.6f} |"
        )
    lines += [
        "",
        "Los 22 modelos históricos conservan Holm55 de la comparación E3 anterior; los tres",
        "candidatos nuevos se contrastan en una familia separada Holm12, cuyos p-valores aparecen abajo.",
        "",
        "## Métricas test de las variantes y sus referencias",
        "",
        "Esta tabla de seis modelos facilita comparar los candidatos con XGBoost original y con los dos",
        "mejores comparadores previos. p Holm12 se muestra solo para cada contraste candidato–XGBoost.",
        "",
        "| Modelo | RMSE | MAE | MAPE (%) | R² | ΔRMSE vs XGBoost | p Holm12 vs XGBoost |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in candidate_ranking.to_dict("records"):
        p_value = row.get("p_Holm_family_12")
        p_text = f"{p_value:.5f}" if pd.notna(p_value) else "—"
        lines.append(
            f"| {row['Modelo']} | {row['RMSE_test']:.6f} | {row['MAE_test']:.6f} | "
            f"{row['MAPE_test']:.4f} | {row['R2_test']:.6f} | "
            f"{row['delta_RMSE_vs_XGBoost']:+.6f} | {p_text} |"
        )
    lines += [
        "",
        "## Contrastes pareados",
        "",
        "La familia de 12 incluye cada nueva variante frente a XGBoost, SVR RBF y TabICLv2, más los tres",
        "contrastes entre variantes. Los intervalos son bootstrap por estudiante; RMSE/R² comparten SSE.",
        "",
        "| Candidato | Referencia | ΔRMSE | IC95% | p bruto | p Holm12 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows.to_dict("records"):
        lines.append(
            f"| {row['Modelo']} | {row['Referencia']} | {row['diferencia_candidato_menos_referencia']:+.6f} | "
            f"[{row['IC_2.5%']:+.6f}, {row['IC_97.5%']:+.6f}] | {row['p_bilateral']:.5f} | "
            f"{row['p_Holm_family_12']:.5f} |"
        )
    lines += ["", "## Validación agrupada", "", "| Modelo | RMSE medio CV | SD | OOF |", "|---|---:|---:|---:|"]
    for key in KEYS:
        for item in report["models"][key]["cv"]:
            if item["metrica"] == "RMSE":
                lines.append(
                    f"| {LABELS[key]} | {item['media_cv']:.6f} | {item['sd_cv']:.6f} | "
                    f"{item['OOF_agrupado']:.6f} |"
                )
    oof_bands = pd.DataFrame(report["oof_by_target_band"])
    lines += [
        "",
        "## Errores OOF por tramo de nota",
        "",
        "Descriptivo y calculado solo con predicciones out-of-fold de train. Sesgo positivo indica subpredicción.",
        "",
        "| Modelo | Tramo | n | RMSE OOF | Sesgo nota−predicción |",
        "|---|---|---:|---:|---:|",
    ]
    for row in oof_bands.to_dict("records"):
        lines.append(
            f"| {row['Modelo']} | {row['Tramo_nota']} | {row['n']} | "
            f"{row['RMSE_OOF']:.6f} | {row['sesgo_nota_menos_prediccion']:+.6f} |"
        )
    baseline_low = oof_bands[(oof_bands.Modelo.eq("XGBoost original")) & oof_bands.Tramo_nota.eq("≤1")]
    dense_low = oof_bands[(oof_bands.Modelo.eq(LABELS["denseweight"])) & oof_bands.Tramo_nota.eq("≤1")]
    baseline_high = oof_bands[(oof_bands.Modelo.eq("XGBoost original")) & oof_bands.Tramo_nota.eq(">4")]
    dense_high = oof_bands[(oof_bands.Modelo.eq(LABELS["denseweight"])) & oof_bands.Tramo_nota.eq(">4")]
    if len(baseline_low) and len(dense_low) and len(baseline_high) and len(dense_high):
        lines += [
            "",
            f"DenseWeight reduce RMSE OOF en ≤1 de {baseline_low.iloc[0].RMSE_OOF:.4f} "
            f"a {dense_low.iloc[0].RMSE_OOF:.4f}, pero en >4 cambia de "
            f"{baseline_high.iloc[0].RMSE_OOF:.4f} a {dense_high.iloc[0].RMSE_OOF:.4f}. "
            "Ese intercambio explica por qué un mejor tail score no garantiza un RMSE global menor.",
        ]
    lines += [
        "",
        "DenseWeight cambia el coste relativo de los errores; una mejora en notas raras puede aumentar",
        "el RMSE global. Para ello se revisan también errores por tramo de nota y no se interpreta esa",
        "ponderación como prueba de mejora global si el RMSE total no baja.",
        "",
    ]
    (OUTPUT_DIR / "resumen.md").write_text("\n".join(lines), encoding="utf-8")


def run(model="all", force=False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train, test, fold_ids, folds, audit = e3_comparison.canonical_partitions()
    signature = provenance()
    if model == "all":
        for key in KEYS:
            run_model(key, signature, train, test, fold_ids, folds, audit, force=force)
        return compare(train, test, signature)
    return run_model(model, signature, train, test, fold_ids, folds, audit, force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=[*KEYS, "all"], default="all")
    parser.add_argument("--force", action="store_true", help="Recalcular folds y resultados de los modelos elegidos.")
    args = parser.parse_args()
    run(model=args.model, force=args.force)
