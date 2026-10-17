"""Evaluación E3 de SVR-RBF y RaFFLE con folds agrupados canónicos.

No reentrena modelos históricos ni consulta el test temporal durante la selección.
Ejecutar desde la raíz del workspace con Precalculo/venv/Scripts/python.exe.
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
from scipy.stats import loguniform, permutation_test
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.svm import SVR
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from entregable3 import (
    BOOK,
    CATEGORICAL,
    FEATURES,
    GROUP,
    NUMERIC,
    OUTPUT,
    PERIOD,
    TARGET,
    grouped_splits,
    load_partitions,
    make_pipeline,
    metrics,
    source_hashes,
    write_json,
)


KEY = "svr_rbf_raffle"
LABELS = {"svr_rbf": "SVR RBF", "raffle": "RaFFLE"}
KEYS = tuple(LABELS)
OUTER_FOLDS = 5
INNER_FOLDS = 5
SEED = 42
SVR_SEARCH_ITERATIONS = 64
SVR_N_JOBS = 4
OUTPUT_DIR = OUTPUT / KEY
PRIVATE_DIR = BOOK / "modelos_preentrenados" / KEY
RAFFLE_VERSION = "0.0.5"
EXPECTED_REFERENCE_COUNT = 11
HISTORICAL_GLOBAL_FAMILY_SIZE = 33
EXPECTED_GLOBAL_FAMILY_SIZE = HISTORICAL_GLOBAL_FAMILY_SIZE + len(KEYS) * EXPECTED_REFERENCE_COUNT

# RandomizedSearchCV opera sobre log-escalas; la selección permanece dentro del
# fit externo. ``gamma='scale'`` y valores explícitos cubren la parametrización
# habitual para datos numéricos escalados más indicadores categóricos one-hot.
SVR_PARAM_DISTRIBUTIONS = {
    "modelo__C": loguniform(1e-3, 1e3),
    "modelo__epsilon": loguniform(1e-2, 1.5),
    "modelo__gamma": ["scale", "auto", *np.logspace(-5, 1, 25).tolist()],
}

# Grilla reducida y fijada antes de mirar el test, derivada de la evaluación
# publicada de RaFFLE. Se mantienen 100 árboles como en el benchmark del paper.
RAFFLE_PARAM_GRID = {
    "modelo__alpha": [0.01, 0.5, 1.0],
    "modelo__n_features_node": [0.7, 1.0],
    "modelo__max_depth": [6, 20],
}
RAFFLE_FIXED = {
    "n_estimators": 100,
    "max_model_depth": 100,
    "min_sample_fit": 10,
    "min_sample_alpha": 5,
    "min_sample_leaf": 5,
    "random_state": SEED,
    "n_features_tree": 1.0,
}


def sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_input_paths() -> dict[str, Path]:
    fine_tuned = sorted((OUTPUT / "tabpfn_25_finetuned").glob("*/test_predictions.csv.gz"))
    if len(fine_tuned) != 1:
        raise ValueError("Se esperaba una sola predicción final de TabPFN fine-tuned.")
    paths = {
        "evaluator": BOOK / "evaluar_svr_rbf_raffle_e3.py",
        "requirements": BOOK / "requirements_svr_rbf_raffle_e3.txt",
        "canonical_train": OUTPUT / "train.csv.gz",
        "canonical_test": OUTPUT / "test.csv.gz",
        "linear_report": OUTPUT / "modelos_lineales.json",
        "linear_fold_metrics": OUTPUT / "fold_metrics.csv",
        "summary_models": OUTPUT / "resumen_completo" / "modelos.csv",
        "scopus_contrasts": OUTPUT / "scopus" / "contrastes_pareados.csv",
        "classic_report": OUTPUT / "clasicos" / "comparacion.json",
        "classic_test_predictions": OUTPUT / "clasicos" / "test_predictions.csv.gz",
        "tabicl_test": OUTPUT / "tabicl_v2" / "test_predictions.csv.gz",
        "tabpfn_test": OUTPUT / "tabpfn_25" / "test_predictions.csv.gz",
        "tabfm_report": OUTPUT / "tabfm" / "reporte.json",
        "tabfm_test": OUTPUT / "tabfm" / "test_predictions.csv.gz",
        "tcr_test": OUTPUT / "tcr_xgboost" / "test_predictions.csv.gz",
        "kernel_ridge_test": OUTPUT / "scopus" / "kernel_ridge" / "test_predictions.csv.gz",
        "catboost_test": OUTPUT / "scopus" / "catboost" / "test_predictions.csv.gz",
        "gpr_report": OUTPUT / "gpr_xgb" / "reporte.json",
        "gpr_test": OUTPUT / "gpr_xgb" / "test_predictions.csv.gz",
        "gpr_contrasts": OUTPUT / "gpr_xgb" / "contrastes_pareados.csv",
        "tabpfn_finetuned_test": fine_tuned[0],
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Faltan insumos E3 requeridos: " + ", ".join(missing))
    return paths


def provenance() -> dict:
    paths = _source_input_paths()
    versions = {
        name: importlib.metadata.version(name)
        for name in [
            "numpy", "pandas", "scikit-learn", "scipy", "statsmodels",
            "fast-model-trees", "joblib",
        ]
    }
    if versions["fast-model-trees"] != RAFFLE_VERSION:
        raise RuntimeError(
            f"Se requiere fast-model-trees=={RAFFLE_VERSION}; se encontró "
            f"{versions['fast-model-trees']}. Instálalo en Precalculo/venv."
        )
    return {
        **source_hashes(),
        "experiment_inputs_sha256": {name: sha256(path) for name, path in paths.items()},
        "versions": versions,
        "configuration": {
            "outer_folds": OUTER_FOLDS,
            "inner_group_folds": INNER_FOLDS,
            "seed": SEED,
            "test_period": 202530,
            "svr_rbf": {
                "kernel": "rbf",
                "search": "RandomizedSearchCV neg_RMSE",
                "n_iter": SVR_SEARCH_ITERATIONS,
                "C": "loguniform(1e-3,1e3)",
                "epsilon": "loguniform(1e-2,1.5)",
                "gamma": "scale, auto, logspace(-5,1,25)",
            },
            "raffle": {
                **RAFFLE_FIXED,
                "alpha": RAFFLE_PARAM_GRID["modelo__alpha"],
                "n_features_node": RAFFLE_PARAM_GRID["modelo__n_features_node"],
                "max_depth": RAFFLE_PARAM_GRID["modelo__max_depth"],
                "categorical_features": CATEGORICAL,
            },
            "preprocessing": {
                "svr_rbf": "pipeline E3 canónico: imputación, log1p/escalado numérico y one-hot",
                "raffle": "mediana numérica; moda y ordinal categórico con índices explícitos; sin escalado",
            },
            "fold_source": "resultados/e3/train.csv.gz, folds externos canónicos de E3",
            "test_used_for_selection": False,
        },
    }


def canonical_partitions():
    """Recupera las filas canónicas y los cinco folds externos ya fijados."""
    train, test, audit = load_partitions()
    baseline = json.loads((OUTPUT / "modelos_lineales.json").read_text(encoding="utf-8"))
    if baseline.get("source_sha256") != source_hashes():
        raise ValueError("La fuente E3 cambió frente a los folds canónicos guardados.")
    for frame, split in ((train, "train"), (test, "test")):
        saved = pd.read_csv(OUTPUT / f"{split}.csv.gz")
        pd.testing.assert_frame_equal(
            frame[FEATURES + [TARGET, PERIOD]],
            saved[FEATURES + [TARGET, PERIOD]],
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
        )
    fold_ids = pd.read_csv(OUTPUT / "train.csv.gz")["fold"].to_numpy(dtype=int)
    if len(fold_ids) != len(train) or set(np.unique(fold_ids)) != set(range(1, OUTER_FOLDS + 1)):
        raise ValueError("Los cinco folds externos canónicos están incompletos.")
    folds = []
    for fold in range(1, OUTER_FOLDS + 1):
        valid = np.flatnonzero(fold_ids == fold)
        fit = np.flatnonzero(fold_ids != fold)
        if not len(valid) or set(train.iloc[fit][GROUP]) & set(train.iloc[valid][GROUP]):
            raise ValueError(f"El fold externo {fold} comparte estudiantes o está vacío.")
        folds.append((fit, valid))
    if set(train[GROUP]) & set(test[GROUP]):
        raise ValueError("Hay estudiantes compartidos entre train y el test temporal.")
    if train[PERIOD].max() >= test[PERIOD].min():
        raise ValueError("El periodo de test debe ser posterior a los periodos de train.")
    return train, test, fold_ids, folds, audit


def _svr_pipeline():
    preprocessing = clone(make_pipeline().named_steps["preprocesamiento"])
    return Pipeline([
        ("preprocesamiento", preprocessing),
        ("modelo", SVR(kernel="rbf", cache_size=128, tol=1e-3)),
    ])


def _raffle_preprocessor():
    """Conserva columnas categóricas como códigos y las marca al estimador."""
    return ColumnTransformer(
        [
            ("num", SimpleImputer(strategy="median"), NUMERIC),
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("ordinal", OrdinalEncoder(
                        handle_unknown="use_encoded_value", unknown_value=-1
                    )),
                ]),
                CATEGORICAL,
            ),
        ],
        remainder="drop",
        sparse_threshold=0,
    )


class RaFFLEE3Regressor(RegressorMixin, BaseEstimator):
    """Adaptador sklearn sobre fast-model-trees; evita clonar el objeto nativo.

    fast-model-trees 0.0.5 transforma internamente df_settings en una lista,
    lo que impide clonar su clase directamente en sklearn 1.9. Este adaptador
    conserva parámetros sin mutarlos y crea un RaFFLE nuevo en cada fit.
    """

    def __init__(
        self,
        n_estimators=100,
        alpha=0.5,
        max_depth=6,
        n_features_node=0.7,
        max_model_depth=100,
        min_sample_fit=10,
        min_sample_alpha=5,
        min_sample_leaf=5,
        random_state=42,
        n_features_tree=1.0,
        categorical_indices=tuple(range(len(NUMERIC), len(FEATURES))),
    ):
        self.n_estimators = n_estimators
        self.alpha = alpha
        self.max_depth = max_depth
        self.n_features_node = n_features_node
        self.max_model_depth = max_model_depth
        self.min_sample_fit = min_sample_fit
        self.min_sample_alpha = min_sample_alpha
        self.min_sample_leaf = min_sample_leaf
        self.random_state = random_state
        self.n_features_tree = n_features_tree
        self.categorical_indices = categorical_indices

    def fit(self, X, y):
        from pilot import RaFFLE

        X = np.asarray(X, dtype=np.float64, order="C")
        y = np.asarray(y, dtype=np.float64).reshape(-1)
        if X.ndim != 2 or X.shape[0] != len(y) or not np.isfinite(X).all() or not np.isfinite(y).all():
            raise ValueError("RaFFLE recibió una matriz no finita o con dimensiones incompatibles.")
        categorical_idx = np.asarray(self.categorical_indices, dtype=np.int64)
        if (categorical_idx < 0).any() or (categorical_idx >= X.shape[1]).any():
            raise ValueError("Los índices categóricos de RaFFLE no coinciden con el preprocesamiento.")
        self.model_ = RaFFLE(
            n_estimators=self.n_estimators,
            alpha=self.alpha,
            max_depth=self.max_depth,
            max_model_depth=self.max_model_depth,
            min_sample_fit=self.min_sample_fit,
            min_sample_alpha=self.min_sample_alpha,
            min_sample_leaf=self.min_sample_leaf,
            random_state=self.random_state,
            n_features_tree=self.n_features_tree,
            n_features_node=self.n_features_node,
            rel_tolerance=0.01,
            precision_scale=1e-10,
        )
        # La versión C++ incluida no implementa n_workers > 1 todavía.
        self.model_.fit(X, y, categorical_idx=categorical_idx, n_workers=1)
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=np.float64, order="C")
        prediction = np.asarray(self.model_.predict(X), dtype=float).reshape(-1)
        if prediction.shape != (len(X),) or not np.isfinite(prediction).all():
            raise ValueError("RaFFLE produjo predicciones inválidas.")
        return prediction


def _raffle_pipeline():
    preprocessing = _raffle_preprocessor()
    estimator = RaFFLEE3Regressor(random_state=SEED)
    return Pipeline([
        ("preprocesamiento", preprocessing),
        ("modelo", estimator),
    ])


def _new_search(key: str, fit_frame: pd.DataFrame):
    inner = grouped_splits(fit_frame, n_splits=INNER_FOLDS)
    if key == "svr_rbf":
        search = RandomizedSearchCV(
            estimator=_svr_pipeline(),
            param_distributions=SVR_PARAM_DISTRIBUTIONS,
            n_iter=SVR_SEARCH_ITERATIONS,
            scoring="neg_root_mean_squared_error",
            cv=inner,
            refit=True,
            n_jobs=SVR_N_JOBS,
            random_state=SEED,
            verbose=1,
            error_score="raise",
            return_train_score=False,
        )
    elif key == "raffle":
        search = GridSearchCV(
            estimator=_raffle_pipeline(),
            param_grid=RAFFLE_PARAM_GRID,
            scoring="neg_root_mean_squared_error",
            cv=inner,
            refit=True,
            n_jobs=1,
            verbose=1,
            error_score="raise",
            return_train_score=False,
        )
    else:
        raise KeyError(key)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Found unknown categories")
        with threadpool_limits(limits=1):
            if key == "svr_rbf":
                with joblib.parallel_backend("loky", inner_max_num_threads=1):
                    search.fit(fit_frame[FEATURES], fit_frame[TARGET].to_numpy(float))
            else:
                search.fit(fit_frame[FEATURES], fit_frame[TARGET].to_numpy(float))
    return search


def _search_table(search, key: str) -> pd.DataFrame:
    frame = pd.DataFrame(search.cv_results_)
    if key == "svr_rbf":
        columns = [
            "params", "mean_test_score", "std_test_score", "rank_test_score",
            "mean_fit_time", "std_fit_time",
        ]
    else:
        columns = [
            "params", "mean_test_score", "std_test_score", "rank_test_score",
            "mean_fit_time", "std_fit_time",
        ]
    return frame[columns].sort_values("rank_test_score")


def _model_directory(key: str) -> Path:
    return OUTPUT_DIR / key


def _private_directory(key: str) -> Path:
    return PRIVATE_DIR / key


def _read_saved_report(path: Path, signature: dict):
    report = json.loads(path.read_text(encoding="utf-8"))
    if not _checkpoint_provenance_matches(report.get("provenance", {}), signature):
        raise ValueError(
            f"La procedencia cambió respecto de {path.name}; preservé los resultados. "
            "Usa --force para recalcularlos en la carpeta del experimento."
        )
    return report


def _checkpoint_provenance_matches(saved: dict, current: dict) -> bool:
    """Permite reanudar folds si cambió solo el código de salida/serialización.

    Entradas, paquetes, protocolo y configuración deben coincidir. El hash del
    evaluador puede cambiar por una corrección posterior al entrenamiento, como
    la incompatibilidad de pickle del wrapper nativo RaFFLE.
    """
    if saved == current:
        return True
    saved = json.loads(json.dumps(saved))
    current = json.loads(json.dumps(current))
    saved_inputs = saved.get("experiment_inputs_sha256", {})
    current_inputs = current.get("experiment_inputs_sha256", {})
    saved_inputs.pop("evaluator", None)
    current_inputs.pop("evaluator", None)
    return saved == current


def run_model(key: str, signature: dict, train, test, fold_ids, folds, partition_audit, force=False):
    folder = _model_directory(key)
    private = _private_directory(key)
    folder.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    report_path = folder / "reporte.json"
    progress_path = folder / "progreso.json"

    if report_path.is_file() and not force:
        report = _read_saved_report(report_path, signature)
        print(f"{LABELS[key]}: reporte válido existente; se reutiliza.", flush=True)
        return report
    if progress_path.is_file() and not force:
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if not _checkpoint_provenance_matches(progress.get("provenance", {}), signature):
            raise ValueError(
                f"La procedencia del progreso de {LABELS[key]} cambió. "
                "Usa --force para recomenzar, preservando el resto de artefactos."
            )

    oof = np.full(len(train), np.nan, dtype=float)
    rows, audits = [], []
    for fold_number, (fit_idx, valid_idx) in enumerate(folds, 1):
        checkpoint_path = folder / f"externo_{fold_number}.json"
        prediction_path = folder / f"oof_{fold_number}.npy"
        if not force and checkpoint_path.is_file() and prediction_path.is_file():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            saved_prediction = np.load(prediction_path)
            if (
                _checkpoint_provenance_matches(checkpoint.get("provenance", {}), signature)
                and len(saved_prediction) == len(valid_idx)
                and np.isfinite(saved_prediction).all()
            ):
                oof[valid_idx] = saved_prediction
                rows.append(checkpoint["metrics"])
                audits.append(checkpoint["audit"])
                print(f"{LABELS[key]}: fold {fold_number}/5 recuperado del checkpoint.", flush=True)
                continue
            raise ValueError(
                f"Checkpoint {checkpoint_path.name} incompleto o con procedencia distinta. "
                "Usa --force para recalcularlo."
            )

        fit_frame = train.iloc[fit_idx]
        valid_frame = train.iloc[valid_idx]
        if set(fit_frame[GROUP]) & set(valid_frame[GROUP]):
            raise ValueError(f"El fold externo {fold_number} mezcla estudiantes.")
        started = time.perf_counter()
        print(
            f"{LABELS[key]}: fold externo {fold_number}/5, ajuste={len(fit_idx)}, "
            f"validación={len(valid_idx)}; inicio de HPO anidado.",
            flush=True,
        )
        search = _new_search(key, fit_frame)
        prediction = np.asarray(search.best_estimator_.predict(valid_frame[FEATURES]), dtype=float)
        if prediction.shape != (len(valid_idx),) or not np.isfinite(prediction).all():
            raise ValueError(f"Predicciones inválidas en {LABELS[key]}, fold {fold_number}.")

        oof[valid_idx] = prediction
        metric_row = {"Modelo": LABELS[key], "Fold": fold_number,
                      **metrics(valid_frame[TARGET], prediction)}
        audit = {
            "fold": fold_number,
            "fit_rows": len(fit_idx),
            "validation_rows": len(valid_idx),
            "fit_students": int(fit_frame[GROUP].nunique()),
            "validation_students": int(valid_frame[GROUP].nunique()),
            "shared_students": 0,
            "best_params": search.best_params_,
            "inner_rmse": float(-search.best_score_),
            "seconds": float(time.perf_counter() - started),
        }
        _search_table(search, key).to_csv(folder / f"busqueda_externa_{fold_number}.csv", index=False)
        np.save(prediction_path, prediction)
        write_json(checkpoint_path, {
            "metrics": metric_row,
            "audit": audit,
            "provenance": signature,
        })
        rows.append(metric_row)
        audits.append(audit)
        write_json(progress_path, {
            "completed_folds": [entry["fold"] for entry in audits],
            "fold_metrics": rows,
            "fold_audit": audits,
            "provenance": signature,
        })
        print(
            f"{LABELS[key]}: fold {fold_number} RMSE={metric_row['RMSE']:.6f}; "
            f"{audit['seconds']:.1f}s; params={search.best_params_}",
            flush=True,
        )
        del search
        gc.collect()

    if not np.isfinite(oof).all():
        raise ValueError(f"Predicciones OOF incompletas para {LABELS[key]}.")
    fold_frame = pd.DataFrame(rows).sort_values("Fold")
    fold_frame.to_csv(folder / "fold_metrics.csv", index=False, encoding="utf-8-sig")

    # Selección final usa exclusivamente train. Este artefacto se escribe antes
    # de consultar el target del periodo temporal reservado.
    print(f"{LABELS[key]}: HPO final en todo train; test aún no evaluado.", flush=True)
    final_progress = json.loads(progress_path.read_text(encoding="utf-8"))
    selection_path = folder / "seleccion_antes_test.json"
    saved_selection = None
    if (
        selection_path.is_file()
        and set(final_progress.get("completed_folds", [])) == set(range(1, OUTER_FOLDS + 1))
        and _checkpoint_provenance_matches(final_progress.get("provenance", {}), signature)
    ):
        candidate_selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection_provenance = candidate_selection.get("provenance", final_progress["provenance"])
        if (
            candidate_selection.get("configuration") == signature["configuration"][key]
            and candidate_selection.get("fold_source") == signature["configuration"]["fold_source"]
            and candidate_selection.get("test_used") is False
            and _checkpoint_provenance_matches(selection_provenance, signature)
            and isinstance(candidate_selection.get("best_params"), dict)
            and "inner_rmse" in candidate_selection
        ):
            saved_selection = candidate_selection

    final_search = None
    if saved_selection is not None:
        pipeline = _svr_pipeline() if key == "svr_rbf" else _raffle_pipeline()
        final_estimator = pipeline.set_params(**saved_selection["best_params"])
        with threadpool_limits(limits=1):
            final_estimator.fit(train[FEATURES], train[TARGET].to_numpy(float))
        final_best_params = saved_selection["best_params"]
        final_inner_rmse = float(saved_selection["inner_rmse"])
        print(
            f"{LABELS[key]}: se recupera la selección final guardada; se reajusta el modelo en train.",
            flush=True,
        )
    else:
        final_search = _new_search(key, train)
        final_estimator = final_search.best_estimator_
        _search_table(final_search, key).to_csv(folder / "busqueda_final.csv", index=False)
        final_best_params = final_search.best_params_
        final_inner_rmse = float(-final_search.best_score_)

    final_selection = {
        "best_params": final_best_params,
        "inner_rmse": final_inner_rmse,
        "configuration": signature["configuration"][key],
        "test_used": False,
        "fold_source": signature["configuration"]["fold_source"],
        "provenance": signature,
    }
    selection_path.write_text(
        json.dumps(final_selection, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    if key == "svr_rbf":
        model_path = private / "modelo_final.joblib"
        temporary_model_path = private / "modelo_final.joblib.tmp"
        try:
            joblib.dump(final_estimator, temporary_model_path)
            temporary_model_path.replace(model_path)
        except Exception:
            temporary_model_path.unlink(missing_ok=True)
            raise
        model_serialization = {"saved": True, "path": str(model_path)}
    else:
        model_serialization = {
            "saved": False,
            "reason": (
                "fast-model-trees==0.0.5 contiene estimadores PILOTWrapper nativos "
                "que no se pueden serializar con pickle/joblib."
            ),
        }
        print(
            "RaFFLE: el paquete no permite serializar PILOTWrapper; continúo con "
            "predicción y métricas. Los parámetros finales quedaron guardados.",
            flush=True,
        )
    final_selection["model_serialization"] = model_serialization
    write_json(selection_path, final_selection)

    # Primer uso predictivo del test se hace después de cerrar el HPO final.
    test_prediction = np.asarray(final_estimator.predict(test[FEATURES]), dtype=float)
    if test_prediction.shape != (len(test),) or not np.isfinite(test_prediction).all():
        raise ValueError(f"Predicciones test inválidas para {LABELS[key]}.")
    test_score = metrics(test[TARGET], test_prediction)
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
        "test": test_score,
        "cv": [
            {
                "metrica": metric,
                "media_cv": float(fold_frame[metric].mean()),
                "sd_cv": float(fold_frame[metric].std(ddof=0)),
                "OOF_agrupado": metrics(train[TARGET], oof)[metric],
            }
            for metric in test_score
        ],
        "best_params": final_best_params,
        "inner_rmse": final_inner_rmse,
        "model_serialization": model_serialization,
        "fold_audit": audits,
        "final_fit_audit": {
            "fit_rows": len(train),
            "fit_students": int(train[GROUP].nunique()),
            "test_rows": len(test),
            "test_students": int(test[GROUP].nunique()),
            "shared_students": 0,
        },
        "partition": partition_audit,
        "provenance": signature,
        "features": FEATURES,
        "target": TARGET,
        "test_used_for_selection": False,
        "method": (
            "5 folds externos canónicos y 5 internos GroupKFold por estudiante; "
            "preprocesamiento dentro de cada fit; selección por RMSE sólo en train; "
            "test temporal 202530 al final."
        ),
        "limitations": [
            "El test temporal ya fue consultado en experimentos anteriores; la inferencia es exploratoria.",
            "Los resultados de validación publicados por los artículos usan particiones aleatorias, no la estructura por estudiante/periodo de E3.",
        ],
    }
    write_json(report_path, report)
    write_json(progress_path, {
        "completed_folds": list(range(1, OUTER_FOLDS + 1)),
        "fold_metrics": rows,
        "fold_audit": audits,
        "test_complete": True,
        "provenance": signature,
    })
    print(f"{LABELS[key]} TEST: {test_score}", flush=True)
    del final_estimator
    if final_search is not None:
        del final_search
    gc.collect()
    return report


def _validate_classic_baseline():
    classic_report_path = OUTPUT / "clasicos" / "comparacion.json"
    classic_report = json.loads(classic_report_path.read_text(encoding="utf-8"))
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
    if classic_report.get("source_sha256") != expected:
        raise ValueError("Predicciones XGBoost no corresponden a la fuente/protocolo E3 actual.")
    frame = pd.read_csv(OUTPUT / "clasicos" / "test_predictions.csv.gz")
    if "xgboost" not in frame or len(frame) == 0:
        raise ValueError("No se encontró la predicción XGBoost canónica.")
    return frame["xgboost"].to_numpy(float)


def _validate_reference_frame(frame: pd.DataFrame, name: str, test: pd.DataFrame,
                              prediction_column="prediccion") -> np.ndarray:
    if len(frame) != len(test) or prediction_column not in frame:
        raise ValueError(f"Predicciones de referencia incompletas: {name}.")
    for column in (TARGET, PERIOD):
        if column not in frame or not np.array_equal(frame[column].to_numpy(), test[column].to_numpy()):
            raise ValueError(f"El archivo de {name} no está alineado con el test E3 en {column}.")
    if "fila_fuente" in frame and not np.array_equal(
        frame["fila_fuente"].to_numpy(), test["fila_fuente"].to_numpy()
    ):
        raise ValueError(f"fila_fuente no coincide para {name}.")
    prediction = frame[prediction_column].to_numpy(dtype=float)
    if prediction.shape != (len(test),) or not np.isfinite(prediction).all():
        raise ValueError(f"Predicciones no finitas o desalineadas en {name}.")
    return prediction


def reference_predictions(test: pd.DataFrame):
    """Valida y alinea los modelos E3 ya calculados para el contraste final."""
    svm_frame = pd.read_csv(OUTPUT / "test.csv.gz")
    svm = _validate_reference_frame(svm_frame, "SVM lineal", test, "svm")
    xgb = _validate_classic_baseline()

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
        raise ValueError("Se esperaba una ejecución final de TabPFN fine-tuned.")
    paths["TabPFN 2.5 fine-tuned"] = fine_tuned[0]

    refs = {"SVM lineal": svm, "XGBoost": xgb}
    for name, path in paths.items():
        refs[name] = _validate_reference_frame(pd.read_csv(path), name, test)

    gpr_frame = pd.read_csv(OUTPUT / "gpr_xgb" / "test_predictions.csv.gz")
    refs["GPR–XGBoost (OOF agrupado)"] = _validate_reference_frame(
        gpr_frame, "GPR–XGBoost", test, "prediccion"
    )
    refs["GPR sola"] = _validate_reference_frame(
        gpr_frame, "GPR sola", test, "gpr_solo_prediccion"
    )
    return refs


def paired_comparison(y, new, old, groups, seed=SEED):
    """Permutación del SSE y bootstrap por estudiante como en E3 previo."""
    codes, ids = pd.factorize(groups, sort=False)
    aggregate = lambda values: np.bincount(codes, weights=values, minlength=len(ids))
    new_sse = aggregate((y - new) ** 2)
    old_sse = aggregate((y - old) ** 2)
    test = permutation_test(
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
            raise ValueError("Varianza nula en el bootstrap pareado por estudiante.")
        rmse_delta.extend(np.sqrt(sse_new / count) - np.sqrt(sse_old / count))
        r2_delta.extend((sse_old - sse_new) / sst)

    new_metrics, old_metrics = metrics(y, new), metrics(y, old)
    rmse_ci = np.quantile(rmse_delta, [0.025, 0.975])
    r2_ci = np.quantile(r2_delta, [0.025, 0.975])
    return [
        {
            "metrica": "RMSE",
            "diferencia_candidato_menos_referencia": new_metrics["RMSE"] - old_metrics["RMSE"],
            "IC_2.5%": float(rmse_ci[0]),
            "IC_97.5%": float(rmse_ci[1]),
            "p_bilateral": float(test.pvalue),
        },
        {
            "metrica": "R²",
            "diferencia_candidato_menos_referencia": new_metrics["R²"] - old_metrics["R²"],
            "IC_2.5%": float(r2_ci[0]),
            "IC_97.5%": float(r2_ci[1]),
            "p_bilateral": float(test.pvalue),
        },
        {
            "metrica": "MAE",
            "diferencia_candidato_menos_referencia": new_metrics["MAE"] - old_metrics["MAE"],
            "IC_2.5%": None,
            "IC_97.5%": None,
            "p_bilateral": None,
        },
        {
            "metrica": "MAPE (%)",
            "diferencia_candidato_menos_referencia": new_metrics["MAPE (%)"] - old_metrics["MAPE (%)"],
            "IC_2.5%": None,
            "IC_97.5%": None,
            "p_bilateral": None,
        },
    ]


def _historical_pvalues(candidate_comparisons):
    """Construye la familia acumulada de 55 contrastes E3 sin duplicar RMSE/R²."""
    previous = pd.read_csv(OUTPUT / "resumen_completo" / "modelos.csv")
    previous = previous[previous["Modelo"].ne("SVM lineal")]
    previous_svm_p = previous["p_bilateral"].dropna().to_numpy(float)

    scopus = pd.read_csv(OUTPUT / "scopus" / "contrastes_pareados.csv")
    prior_xgb_p = scopus.loc[
        scopus["Referencia"].eq("XGBoost") & scopus["metrica"].eq("RMSE"),
        "p_bilateral",
    ].dropna().to_numpy(float)

    tabfm_report = json.loads((OUTPUT / "tabfm" / "reporte.json").read_text(encoding="utf-8"))
    tabfm_p = np.asarray([
        comparison["rows"][0]["p_bilateral"]
        for comparison in tabfm_report["paired_comparisons"]
    ], dtype=float)

    gpr_contrasts = pd.read_csv(OUTPUT / "gpr_xgb" / "contrastes_pareados.csv")
    gpr_p = gpr_contrasts.loc[gpr_contrasts["metrica"].eq("RMSE"), "p_bilateral"].dropna().to_numpy(float)

    current_rows = [
        (model, reference, rows[0]["p_bilateral"])
        for model, comparisons in candidate_comparisons.items()
        for reference, rows in comparisons.items()
    ]
    current_p = np.asarray([row[2] for row in current_rows], dtype=float)
    expected_current = len(KEYS) * EXPECTED_REFERENCE_COUNT
    if (
        len(previous_svm_p) != 17
        or len(prior_xgb_p) != 4
        or len(tabfm_p) != 2
        or len(gpr_p) != 10
        or len(current_p) != expected_current
    ):
        raise ValueError(
            f"La familia acumulada esperada es {EXPECTED_GLOBAL_FAMILY_SIZE} contrastes: "
            "17 previos vs SVM, 4 Scopus vs XGBoost, 2 TabFM, 10 GPR/ablación "
            f"y {expected_current} candidatos (11 referencias por candidato). "
            f"Recibidos: {len(previous_svm_p)}, {len(prior_xgb_p)}, {len(tabfm_p)}, "
            f"{len(gpr_p)}, {len(current_p)}."
        )

    all_p = np.r_[previous_svm_p, prior_xgb_p, tabfm_p, gpr_p, current_p]
    if len(all_p) != EXPECTED_GLOBAL_FAMILY_SIZE:
        raise ValueError(f"Se esperaban {EXPECTED_GLOBAL_FAMILY_SIZE} p-valores globales; hay {len(all_p)}.")
    adjusted = multipletests(all_p, method="holm")[1]
    family_vs_svm = np.r_[
        previous_svm_p,
        tabfm_p[0],
        gpr_p[0],
        [comparisons["SVM lineal"][0]["p_bilateral"] for comparisons in candidate_comparisons.values()],
    ]
    holm_vs_svm = multipletests(family_vs_svm, method="holm")[1]
    candidate_offset = len(previous_svm_p) + len(prior_xgb_p) + len(tabfm_p) + len(gpr_p)
    candidate_holm_global = adjusted[candidate_offset:]

    global_by_pair = {}
    for (model, reference, _), value in zip(current_rows, candidate_holm_global):
        global_by_pair[(model, reference)] = float(value)
    svm_by_model = {
        model: float(value)
        for model, value in zip(candidate_comparisons.keys(), holm_vs_svm[-len(candidate_comparisons):])
    }
    return {
        "historical_previous": previous,
        "previous_svm_p": previous_svm_p,
        "prior_xgb_p": prior_xgb_p,
        "tabfm_p": tabfm_p,
        "gpr_p": gpr_p,
        "all_adjusted": adjusted,
        "holm_vs_svm": holm_vs_svm,
        "candidate_global": global_by_pair,
        "candidate_vs_svm": svm_by_model,
        "candidate_offset": int(candidate_offset),
        "family_size_vs_svm": int(len(family_vs_svm)),
        "family_size_global": int(len(all_p)),
    }


def compare(train, test, signature):
    candidate_reports = {}
    for key in KEYS:
        path = _model_directory(key) / "reporte.json"
        if not path.is_file():
            raise FileNotFoundError(f"Ejecuta primero ambos modelos; falta {path}.")
        candidate_reports[key] = _read_saved_report(path, signature)

    references = reference_predictions(test)
    y = test[TARGET].to_numpy(float)
    predictions = {}
    candidate_comparisons = {}

    for key in KEYS:
        prediction_frame = pd.read_csv(_model_directory(key) / "test_predictions.csv.gz")
        prediction = _validate_reference_frame(prediction_frame, LABELS[key], test)
        predictions[key] = prediction
        candidate_comparisons[key] = {}
        for reference, reference_prediction in references.items():
            rows = paired_comparison(y, prediction, reference_prediction, test[GROUP])
            candidate_comparisons[key][reference] = rows

    direct_candidate_rows = paired_comparison(
        y, predictions["svr_rbf"], predictions["raffle"], test[GROUP]
    )

    correction = _historical_pvalues(candidate_comparisons)
    all_contrasts = []
    for key in KEYS:
        for reference, rows in candidate_comparisons[key].items():
            for row in rows:
                p = row["p_bilateral"]
                row["p_Holm_global_55"] = (
                    correction["candidate_global"][(key, reference)] if p is not None else None
                )
                row["significativa_al_5%_Holm"] = bool(
                    row["p_Holm_global_55"] is not None and row["p_Holm_global_55"] < 0.05
                )
                row["p_Holm_vs_SVM_21"] = (
                    correction["candidate_vs_svm"][key]
                    if p is not None and reference == "SVM lineal"
                    else None
                )
                all_contrasts.append({
                    "Modelo": LABELS[key],
                    "Referencia": reference,
                    **row,
                })

    contrast_frame = pd.DataFrame(all_contrasts)
    contrast_frame.to_csv(OUTPUT_DIR / "contrastes_pareados.csv", index=False, encoding="utf-8-sig")

    previous = pd.read_csv(OUTPUT / "resumen_completo" / "modelos.csv")
    ranking = previous[["Modelo", "RMSE_test", "p_bilateral"]].copy()
    tabfm_report = json.loads((OUTPUT / "tabfm" / "reporte.json").read_text(encoding="utf-8"))
    gpr_report = json.loads((OUTPUT / "gpr_xgb" / "reporte.json").read_text(encoding="utf-8"))
    extras = [
        {"Modelo": tabfm_report["model"], "RMSE_test": tabfm_report["test"]["RMSE"],
         "p_bilateral": tabfm_report["paired_comparisons"][0]["rows"][0]["p_bilateral"]},
        {"Modelo": gpr_report["model"], "RMSE_test": gpr_report["test"]["RMSE"],
         "p_bilateral": gpr_report["paired_comparisons"][0]["rows"][0]["p_bilateral"]},
    ]
    for key in KEYS:
        extras.append({
            "Modelo": LABELS[key],
            "RMSE_test": candidate_reports[key]["test"]["RMSE"],
            "p_bilateral": candidate_comparisons[key]["SVM lineal"][0]["p_bilateral"],
        })
    ranking = pd.concat([ranking, pd.DataFrame(extras)], ignore_index=True)
    svm_prediction = references["SVM lineal"]
    svm_rmse = metrics(y, svm_prediction)["RMSE"]
    ranking["delta_RMSE_vs_SVM"] = ranking["RMSE_test"] - svm_rmse
    ranking["p_Holm_vs_SVM_21"] = np.nan
    previous_no_svm = previous[previous["Modelo"].ne("SVM lineal")]
    previous_svm_adjusted = correction["holm_vs_svm"][:len(previous_no_svm)]
    previous_by_model = dict(zip(previous_no_svm["Modelo"], previous_svm_adjusted))
    for index, model in ranking["Modelo"].items():
        if model in previous_by_model:
            ranking.loc[index, "p_Holm_vs_SVM_21"] = previous_by_model[model]
    ranking.loc[ranking["Modelo"].eq(tabfm_report["model"]), "p_Holm_vs_SVM_21"] = correction["holm_vs_svm"][17]
    ranking.loc[ranking["Modelo"].eq(gpr_report["model"]), "p_Holm_vs_SVM_21"] = correction["holm_vs_svm"][18]
    for key in KEYS:
        ranking.loc[ranking["Modelo"].eq(LABELS[key]), "p_Holm_vs_SVM_21"] = correction["candidate_vs_svm"][key]

    ranking["p_Holm_global_55"] = np.nan
    adjusted = correction["all_adjusted"]
    for index, model in ranking["Modelo"].items():
        matches = previous_no_svm.index[previous_no_svm["Modelo"].eq(model)].tolist()
        if matches:
            original_position = previous_no_svm.index.get_loc(matches[0])
            ranking.loc[index, "p_Holm_global_55"] = adjusted[original_position]
    ranking.loc[ranking["Modelo"].eq("SVM lineal"), "p_Holm_global_55"] = np.nan
    ranking.loc[ranking["Modelo"].eq(tabfm_report["model"]), "p_Holm_global_55"] = adjusted[17 + 4]
    ranking.loc[ranking["Modelo"].eq(gpr_report["model"]), "p_Holm_global_55"] = adjusted[17 + 4 + 2]
    # La primera comparación de cada candidato es contra SVM, orden en KEYS.
    current_offset = correction["candidate_offset"]
    for candidate_index, key in enumerate(KEYS):
        ranking.loc[ranking["Modelo"].eq(LABELS[key]), "p_Holm_global_55"] = adjusted[
            current_offset + candidate_index * len(references)
        ]

    ranking = ranking.sort_values("RMSE_test").reset_index(drop=True)
    ranking.insert(0, "rango_RMSE", np.arange(1, len(ranking) + 1))
    ranking.to_csv(OUTPUT_DIR / "ranking_rmse_test.csv", index=False, encoding="utf-8-sig")

    for key in KEYS:
        if not isinstance(candidate_reports[key].get("model_serialization"), dict):
            model_path = _private_directory(key) / "modelo_final.joblib"
            candidate_reports[key]["model_serialization"] = (
                {"saved": True, "path": str(model_path)}
                if model_path.is_file()
                else {
                    "saved": False,
                    "reason": "No hay un artefacto serializado del estimador final.",
                }
            )
        candidate_reports[key]["paired_comparisons"] = [
            {"referencia": ref, "rows": candidate_comparisons[key][ref]}
            for ref in references
        ]
        candidate_reports[key]["family_size_vs_svm"] = correction["family_size_vs_svm"]
        candidate_reports[key]["family_size_global"] = correction["family_size_global"]
        candidate_reports[key]["test_used_for_selection"] = False
        write_json(_model_directory(key) / "reporte.json", candidate_reports[key])

    report = {
        "models": candidate_reports,
        "ranking": ranking.to_dict("records"),
        "contrasts": contrast_frame.to_dict("records"),
        "direct_candidate_comparison": {
            "model": LABELS["svr_rbf"],
            "reference": LABELS["raffle"],
            "rows": direct_candidate_rows,
            "multiplicity_note": (
                "Contraste adicional exploratorio; no incluido en la familia Holm global de 55."
            ),
        },
        "family_size_vs_svm": correction["family_size_vs_svm"],
        "family_size_global": correction["family_size_global"],
        "references": list(references),
        "statistics": (
            "Permutación pareada sobre SSE por estudiante: 99.999 reasignaciones; "
            "bootstrap por estudiante: 10.000; semilla 42. RMSE y R² comparten "
            "contraste SSE. Holm global extiende la familia E3 acumulada de 33 a 55. "
            "El contraste directo entre los dos candidatos se reporta aparte y sin ajuste Holm."
        ),
        "test_used_for_selection": False,
        "caveat": "El test temporal 202530 ya fue consultado en trabajos previos; inferencia exploratoria.",
        "provenance": signature,
    }
    write_json(OUTPUT_DIR / "reporte.json", report)
    _write_summary(report, contrast_frame)
    print(ranking.to_string(index=False), flush=True)
    print(contrast_frame.loc[contrast_frame["metrica"].eq("RMSE")].to_string(index=False), flush=True)
    return report


def _write_summary(report, contrasts: pd.DataFrame):
    ranking = pd.DataFrame(report["ranking"])
    rmse_contrasts = contrasts[contrasts["metrica"].eq("RMSE")]
    lines = [
        "# SVR RBF y RaFFLE en E3",
        "",
        "Evaluación con cinco folds externos canónicos y cinco folds internos GroupKFold por estudiante.",
        "La preparación se ajusta dentro de cada fit; el test temporal 202530 se predice al final.",
        "La inferencia del test es exploratoria porque ese periodo ya se consultó en experimentos anteriores.",
        "",
        "## Métricas y ranking temporal",
        "",
        "| Rango | Modelo | RMSE test | Δ RMSE vs. SVM | Holm vs. SVM (21) | Holm global (55) |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in ranking.to_dict("records"):
        p_svm = row.get("p_Holm_vs_SVM_21")
        p_global = row.get("p_Holm_global_55")
        lines.append(
            f"| {int(row['rango_RMSE'])} | {row['Modelo']} | {row['RMSE_test']:.6f} | "
            f"{row['delta_RMSE_vs_SVM']:+.6f} | "
            f"{'—' if pd.isna(p_svm) else f'{p_svm:.5f}'} | "
            f"{'—' if pd.isna(p_global) else f'{p_global:.5f}'} |"
        )
    lines.extend([
        "",
        "## Contrastes pareados en test",
        "",
        "ΔRMSE negativo favorece al candidato. Los intervalos son marginales; Holm corrige la familia acumulada.",
        "",
        "| Candidato | Referencia | Δ RMSE | IC95% | p bilateral | p Holm global 55 |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in rmse_contrasts.to_dict("records"):
        lines.append(
            f"| {row['Modelo']} | {row['Referencia']} | "
            f"{row['diferencia_candidato_menos_referencia']:+.6f} | "
            f"[{row['IC_2.5%']:+.6f}, {row['IC_97.5%']:+.6f}] | "
            f"{row['p_bilateral']:.5f} | {row['p_Holm_global_55']:.5f} |"
        )
    lines.extend([
        "",
        "## Contraste directo entre SVR RBF y RaFFLE",
        "",
        "Análisis adicional exploratorio, no incluido en la familia Holm global de 55 contrastes.",
        "",
        "| Métrica | SVR RBF menos RaFFLE | IC95% | p bilateral sin ajuste |",
        "|---|---:|---:|---:|",
    ])
    for row in report["direct_candidate_comparison"]["rows"]:
        if row["metrica"] in ("RMSE", "R²"):
            lines.append(
                f"| {row['metrica']} | {row['diferencia_candidato_menos_referencia']:+.6f} | "
                f"[{row['IC_2.5%']:+.6f}, {row['IC_97.5%']:+.6f}] | "
                f"{row['p_bilateral']:.5f} |"
            )
    lines.extend([
        "",
        "## Métricas de validación agrupada",
        "",
        "| Modelo | Métrica | Media 5 folds | SD | OOF agrupado |",
        "|---|---|---:|---:|---:|",
    ])
    for key in KEYS:
        model_report = report["models"][key]
        for item in model_report["cv"]:
            lines.append(
                f"| {model_report['model']} | {item['metrica']} | {item['media_cv']:.6f} | "
                f"{item['sd_cv']:.6f} | {item['OOF_agrupado']:.6f} |"
            )
    lines.extend([
        "",
        "La prueba pareada permuta SSE agregado por estudiante (99.999 reasignaciones); el bootstrap también remuestrea estudiantes (10.000 réplicas). RMSE y R² comparten contraste y no se cuentan como pruebas independientes.",
        "",
    ])
    (OUTPUT_DIR / "resumen.md").write_text("\n".join(lines), encoding="utf-8")


def run(model="all", force=False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train, test, fold_ids, folds, partition_audit = canonical_partitions()
    signature = provenance()
    if model == "all":
        for key in KEYS:
            run_model(key, signature, train, test, fold_ids, folds, partition_audit, force=force)
        return compare(train, test, signature)
    return run_model(model, signature, train, test, fold_ids, folds, partition_audit, force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=[*KEYS, "all"], default="all")
    parser.add_argument("--force", action="store_true", help="Recalcular folds y test; sobrescribe solo esta ejecución.")
    args = parser.parse_args()
    run(model=args.model, force=args.force)
