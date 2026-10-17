"""Evaluación E3 de LinXGBoost con hojas lineales regularizadas.

Implementación independiente inspirada en de Vito (2017,
https://arxiv.org/abs/1710.03634). Por la mezcla y cardinalidad de las variables
E3, las hojas ajustan Ridge sobre todas las columnas numéricas y categóricas
one-hot, escaladas dentro de cada fit. Las divisiones continuas se aproximan
con hasta 12 cortes por cuantiles; los indicadores categóricos usan su corte
binario exacto.
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
from scipy.stats import loguniform
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from entregable3 import (
    BOOK,
    FEATURES,
    GROUP,
    OUTPUT as E3_OUTPUT,
    TARGET,
    grouped_splits,
    make_pipeline,
    metrics,
    write_json,
)
import evaluar_svr_rbf_raffle_e3 as e3_comparison


KEY = "linxgboost"
LABEL = "LinXGBoost (hojas completas E3)"
SEED = 42
OUTER_FOLDS = 5
INNER_FOLDS = 5
SEARCH_ITERATIONS = 20
N_JOBS = 4
MAX_BINS = 12
OUTPUT_DIR = E3_OUTPUT / KEY

PARAM_DISTRIBUTIONS = {
    "modelo__n_estimators": [1, 2, 3, 5],
    "modelo__learning_rate": [0.03, 0.06, 0.10, 0.16, 0.22],
    "modelo__max_depth": [2, 3, 4],
    "modelo__min_samples_leaf": [80, 120, 160, 220],
    "modelo__reg_lambda": loguniform(0.1, 100.0),
    "modelo__gamma": [0.0, 0.05, 0.2, 1.0],
}


def sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class LinXGBoostRegressor(RegressorMixin, BaseEstimator):
    """Gradient boosting whose leaves fit regularized local linear residuals.

    The split score is the second-order squared-error reduction from the
    paper's local linear objective. Every column in E3's fold-local encoded
    design is included in each regularized local model and in split search.
    """

    def __init__(
        self,
        n_estimators=2,
        learning_rate=0.1,
        max_depth=3,
        min_samples_leaf=120,
        reg_lambda=10.0,
        gamma=0.0,
        max_bins=MAX_BINS,
        n_linear_features=None,
        random_state=SEED,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.reg_lambda = reg_lambda
        self.gamma = gamma
        self.max_bins = max_bins
        self.n_linear_features = n_linear_features
        self.random_state = random_state

    def _leaf_solution(self, gram, cross):
        # For square loss the reference uses C=2 X'X + lbda P. Dividing
        # through by two gives this Ridge system, with an unpenalized bias.
        matrix = gram + (0.5 * self.reg_lambda) * self._penalty_
        n = float(gram[-1, -1])
        d = gram.shape[0] - 1
        if n <= d:
            coef = np.zeros(d + 1, dtype=np.float64)
            coef[-1] = cross[-1] / max(n, 1.0)
            return coef, float(cross @ coef)
        try:
            condition = np.linalg.cond(matrix)
            if not np.isfinite(condition) or condition > 1e12:
                raise np.linalg.LinAlgError("ill-conditioned local linear leaf")
            coef = np.linalg.solve(matrix, cross)
        except np.linalg.LinAlgError:
            # The author falls back to a constant leaf when the linear system
            # is too ill-conditioned.
            coef = np.zeros(d + 1, dtype=np.float64)
            coef[-1] = cross[-1] / max(n, 1.0)
        score = float(cross @ coef)
        return coef, score

    def _candidate_positions(self, sorted_values):
        n = len(sorted_values)
        boundaries = np.flatnonzero(sorted_values[:-1] < sorted_values[1:]) + 1
        boundaries = boundaries[
            (boundaries >= self.min_samples_leaf)
            & (boundaries <= n - self.min_samples_leaf)
        ]
        if not len(boundaries):
            return boundaries
        if len(boundaries) > self.max_bins:
            sample = np.rint(np.linspace(0, len(boundaries) - 1, self.max_bins)).astype(int)
            boundaries = boundaries[np.unique(sample)]
        return boundaries

    def _best_split(self, X, Z, residual, indices, parent_score):
        node_X = X[indices]
        node_Z = Z[indices]
        node_residual = residual[indices]
        n = len(indices)
        best = None

        for feature in range(X.shape[1]):
            order = np.argsort(node_X[:, feature], kind="mergesort")
            sorted_values = node_X[order, feature]
            boundaries = self._candidate_positions(sorted_values)
            if not len(boundaries):
                continue

            sorted_Z = node_Z[order]
            sorted_residual = node_residual[order]
            prefix_gram = np.einsum("ni,nj->nij", sorted_Z, sorted_Z, optimize=True).cumsum(axis=0)
            prefix_cross = np.cumsum(sorted_Z * sorted_residual[:, None], axis=0)

            gram_left = prefix_gram[boundaries - 1]
            cross_left = prefix_cross[boundaries - 1]
            gram_right = prefix_gram[-1] - gram_left
            cross_right = prefix_cross[-1] - cross_left

            penalty = (0.5 * self.reg_lambda) * self._penalty_
            try:
                coef_left = np.linalg.solve(gram_left + penalty, cross_left[..., None])[..., 0]
                coef_right = np.linalg.solve(gram_right + penalty, cross_right[..., None])[..., 0]
            except np.linalg.LinAlgError:
                # Keep the vectorized quantile search practical; observed
                # candidate matrices remain Ridge-regularized and solvable.
                coef_left = np.stack([
                    np.linalg.lstsq(gram + penalty, cross, rcond=None)[0]
                    for gram, cross in zip(gram_left, cross_left)
                ])
                coef_right = np.stack([
                    np.linalg.lstsq(gram + penalty, cross, rcond=None)[0]
                    for gram, cross in zip(gram_right, cross_right)
                ])
            score_left = np.einsum("ij,ij->i", cross_left, coef_left)
            score_right = np.einsum("ij,ij->i", cross_right, coef_right)
            gains = score_left + score_right - parent_score - self.gamma

            choice = int(np.argmax(gains))
            gain = float(gains[choice])
            if best is None or gain > best["gain"]:
                boundary = int(boundaries[choice])
                low = float(sorted_values[boundary - 1])
                high = float(sorted_values[boundary])
                best = {
                    "feature": feature,
                    "threshold": low + (high - low) / 2.0,
                    "gain": gain,
                    "boundary": boundary,
                }
        return best

    def _grow(self, X, Z, residual, indices, depth):
        local_Z = Z[indices]
        local_residual = residual[indices]
        gram = local_Z.T @ local_Z
        cross = local_Z.T @ local_residual
        coef, parent_score = self._leaf_solution(gram, cross)
        node = {
            "feature": None,
            "coef": coef,
            "obj": -parent_score,
            "gain": float("-inf"),
        }

        # The author's root node has depth 1 and stops at depth >= max_depth.
        if depth >= self.max_depth or len(indices) < 2 * self.min_samples_leaf:
            return node

        split = self._best_split(X, Z, residual, indices, parent_score)
        if split is None:
            return node
        values = X[indices, split["feature"]]
        left_idx = indices[values <= split["threshold"]]
        right_idx = indices[values > split["threshold"]]
        if min(len(left_idx), len(right_idx)) < self.min_samples_leaf:
            return node

        left = self._grow(X, Z, residual, left_idx, depth + 1)
        right = self._grow(X, Z, residual, right_idx, depth + 1)
        node.update({
            "feature": split["feature"],
            "threshold": split["threshold"],
            "gain": split["gain"],
            "left": left,
            "right": right,
        })
        return node

    def _tree_objective(self, node):
        if node["feature"] is None:
            return node["obj"] + self.gamma
        return self._tree_objective(node["left"]) + self._tree_objective(node["right"])

    def _prune_tree(self, node):
        """Match the author's negative-gain, objective-based pruning pass."""
        if node["feature"] is None:
            return
        if node["gain"] < 0 and node["obj"] < self._tree_objective(node):
            node["feature"] = None
            node.pop("threshold", None)
            node.pop("left", None)
            node.pop("right", None)
            return
        self._prune_tree(node["left"])
        self._prune_tree(node["right"])

    def _predict_tree(self, node, X, Z, indices, output):
        if node["feature"] is None:
            output[indices] = Z[indices] @ node["coef"]
            return
        mask = X[indices, node["feature"]] <= node["threshold"]
        self._predict_tree(node["left"], X, Z, indices[mask], output)
        self._predict_tree(node["right"], X, Z, indices[~mask], output)

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1)
        if X.ndim != 2 or X.shape[0] != len(y) or not np.isfinite(X).all() or not np.isfinite(y).all():
            raise ValueError("X e y deben ser finitos, bidimensional y de igual longitud.")
        if self.n_linear_features is not None and not 1 <= self.n_linear_features <= X.shape[1]:
            raise ValueError("n_linear_features está fuera del ancho de X.")
        if self.reg_lambda <= 0:
            raise ValueError("reg_lambda debe ser positivo para estabilizar las hojas.")
        if self.min_samples_leaf < 2:
            raise ValueError("min_samples_leaf debe ser al menos 2.")

        self.n_linear_features_ = X.shape[1] if self.n_linear_features is None else self.n_linear_features
        numeric = X[:, : self.n_linear_features_]
        self.n_linear_features_ = numeric.shape[1]
        Z = np.column_stack([numeric, np.ones(len(X), dtype=np.float64)])
        self._penalty_ = np.diag(np.r_[np.ones(self.n_linear_features_), 0.0])
        self.n_features_in_ = X.shape[1]
        # The author's reference initializes its running prediction to zero.
        self.init_score_ = 0.0
        prediction = np.zeros(len(y), dtype=np.float64)
        self.trees_ = []

        for _ in range(self.n_estimators):
            residual = y - prediction
            indices = np.arange(len(y), dtype=np.int64)
            tree = self._grow(X, Z, residual, indices, depth=1)
            self._prune_tree(tree)
            # Match the reference: discard a tree with non-improving total
            # objective and stop adding estimators.
            if self._tree_objective(tree) > 0.0:
                break
            increment = np.empty(len(y), dtype=np.float64)
            self._predict_tree(tree, X, Z, indices, increment)
            prediction += self.learning_rate * increment
            self.trees_.append(tree)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 2 or X.shape[1] != self.n_features_in_ or not np.isfinite(X).all():
            raise ValueError("X de predicción no coincide con las características del fit.")
        numeric = X[:, : self.n_linear_features_]
        Z = np.column_stack([numeric, np.ones(len(X), dtype=np.float64)])
        prediction = np.zeros(len(X), dtype=np.float64)
        indices = np.arange(len(X), dtype=np.int64)
        for tree in self.trees_[:-1]:
            increment = np.empty(len(X), dtype=np.float64)
            self._predict_tree(tree, X, Z, indices, increment)
            prediction += self.learning_rate * increment
        if self.trees_:
            increment = np.empty(len(X), dtype=np.float64)
            self._predict_tree(self.trees_[-1], X, Z, indices, increment)
            # The author's public predict() leaves the newest tree unshrunk.
            prediction += increment
        return prediction


def _pipeline():
    preprocessing = clone(make_pipeline().named_steps["preprocesamiento"])
    model = LinXGBoostRegressor(n_linear_features=None, max_bins=MAX_BINS)
    return Pipeline([
        ("preprocesamiento", preprocessing),
        ("escalado_hojas", StandardScaler()),
        ("modelo", model),
    ])


def _search_table(search):
    frame = pd.DataFrame(search.cv_results_)
    params = [column for column in frame if column.startswith("param_")]
    return frame[params + ["mean_test_score", "std_test_score", "rank_test_score", "mean_fit_time"]].assign(
        RMSE=lambda result: -result["mean_test_score"]
    ).sort_values("rank_test_score")


def _new_search(frame):
    return RandomizedSearchCV(
        estimator=_pipeline(),
        param_distributions=PARAM_DISTRIBUTIONS,
        n_iter=SEARCH_ITERATIONS,
        scoring="neg_root_mean_squared_error",
        cv=grouped_splits(frame, n_splits=INNER_FOLDS),
        random_state=SEED,
        n_jobs=N_JOBS,
        refit=True,
        error_score="raise",
        return_train_score=False,
    )


def _configuration():
    return {
        "algorithm": "LinXGBoost, independent implementation of second-order local-linear leaf split gain",
        "outer_folds": OUTER_FOLDS,
        "inner_group_folds": INNER_FOLDS,
        "search_iterations": SEARCH_ITERATIONS,
        "seed": SEED,
        "parameter_distributions": {
            key: ("loguniform(0.1, 100.0)" if key.endswith("reg_lambda") else list(value))
            for key, value in PARAM_DISTRIBUTIONS.items()
        },
        "split_search": f"up to {MAX_BINS} rank-quantile cuts per feature; approximates author's exhaustive continuous thresholds",
        "leaf_linear_features": "all numeric and one-hot columns, rescaled inside each fit",
        "categoricals": "one-hot encoded inside each fit; included in leaf regressions and split candidates",
        "leaf_regularization": "ridge on all local coefficients except the unpenalized intercept",
        "leaf_scaling": "StandardScaler after numeric preprocessing and one-hot encoding, fit within fold",
        "initial_prediction": 0.0,
        "root_depth": 1,
        "last_tree_prediction": "unshrunk at inference, matching author's public predict convention",
        "tree_pruning": "author-style negative-gain pruning by subtree objective; stop if tree objective > 0",
        "lambda_mapping": "author square-loss matrix 2 X'X + lambda P; Ridge system uses lambda/2",
        "root_depth_convention": "root depth=1; nodes stop when depth >= max_depth",
        "initial_leaf_model_fallback": "constant if n <= feature dimension or local system condition number > 1e12",
        "subsample": 1.0,
        "test_period": 202530,
        "test_used_for_selection": False,
    }


def provenance():
    signature = e3_comparison.provenance()
    signature.setdefault("experiment_inputs_sha256", {})["linxgboost_evaluator"] = sha256(__file__)
    signature.setdefault("versions", {})["linxgboost_implementation"] = "independent-e3-author-aligned-v3"
    signature.setdefault("configuration", {})["linxgboost_e3"] = _configuration()
    return signature


def _provenance_matches(saved, current):
    saved = json.loads(json.dumps(saved))
    current = json.loads(json.dumps(current))
    for signature in (saved, current):
        signature.get("experiment_inputs_sha256", {}).pop("linxgboost_evaluator", None)
    return e3_comparison._checkpoint_provenance_matches(saved, current)


def _read_report(path, signature):
    report = json.loads(path.read_text(encoding="utf-8"))
    if not _provenance_matches(report.get("provenance", {}), signature):
        raise ValueError(f"La procedencia de {path} cambió; usa --force para recalcular.")
    return report


def _save_oof(path, train, predictions, fold_ids):
    frame = pd.DataFrame({
        "fold": fold_ids,
        "y_true": train[TARGET].to_numpy(dtype=np.float64),
        "prediction": predictions,
    })
    frame.to_csv(path, index=False, compression="gzip", float_format="%.17g")


def run_model(signature, train, test, folds, partition_audit, force=False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "reporte_modelo.json"
    prediction_path = OUTPUT_DIR / "oof_predictions.csv.gz"
    test_prediction_path = OUTPUT_DIR / "test_predictions.csv.gz"
    if report_path.is_file() and prediction_path.is_file() and test_prediction_path.is_file() and not force:
        report = _read_report(report_path, signature)
        print("LinXGBoost: reporte válido; se reutilizan predicciones guardadas.", flush=True)
        return report

    oof = np.full(len(train), np.nan, dtype=np.float64)
    fold_rows, fold_audits = [], []
    for fold, (fit_idx, valid_idx) in enumerate(folds, 1):
        checkpoint_path = OUTPUT_DIR / f"externo_{fold}.json"
        pred_path = OUTPUT_DIR / f"oof_{fold}.npy"
        if not force and checkpoint_path.is_file() and pred_path.is_file():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            prediction = np.load(pred_path)
            if (
                _provenance_matches(checkpoint.get("provenance", {}), signature)
                and prediction.shape == (len(valid_idx),)
                and np.isfinite(prediction).all()
            ):
                oof[valid_idx] = prediction
                fold_rows.append(checkpoint["metrics"])
                fold_audits.append(checkpoint["audit"])
                print(f"LinXGBoost: fold {fold}/5 recuperado del checkpoint.", flush=True)
                continue
            raise ValueError(f"Checkpoint externo {fold} inválido; usa --force para reiniciarlo.")

        fit_frame, valid_frame = train.iloc[fit_idx], train.iloc[valid_idx]
        if set(fit_frame[GROUP]) & set(valid_frame[GROUP]):
            raise ValueError(f"El fold {fold} mezcla estudiantes.")
        started = time.perf_counter()
        print(
            f"LinXGBoost: fold externo {fold}/5, ajuste={len(fit_idx)}, validación={len(valid_idx)}; HPO anidado.",
            flush=True,
        )
        search = _new_search(fit_frame)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            with threadpool_limits(limits=1), joblib.parallel_backend("loky", inner_max_num_threads=1):
                search.fit(fit_frame[FEATURES], fit_frame[TARGET].to_numpy(dtype=np.float64), groups=fit_frame[GROUP])
        prediction = np.asarray(search.best_estimator_.predict(valid_frame[FEATURES]), dtype=np.float64)
        if prediction.shape != (len(valid_idx),) or not np.isfinite(prediction).all():
            raise ValueError(f"Predicciones inválidas en el fold {fold}.")
        oof[valid_idx] = prediction
        metric_row = {"Modelo": LABEL, "Fold": fold, **metrics(valid_frame[TARGET], prediction)}
        audit = {
            "fold": fold,
            "fit_rows": len(fit_idx),
            "validation_rows": len(valid_idx),
            "fit_students": int(fit_frame[GROUP].nunique()),
            "validation_students": int(valid_frame[GROUP].nunique()),
            "shared_students": 0,
            "inner_folds": INNER_FOLDS,
            "best_params": search.best_params_,
            "inner_rmse": float(-search.best_score_),
            "seconds": float(time.perf_counter() - started),
        }
        _search_table(search).to_csv(OUTPUT_DIR / f"busqueda_externa_{fold}.csv", index=False, encoding="utf-8-sig")
        np.save(pred_path, prediction)
        write_json(checkpoint_path, {"metrics": metric_row, "audit": audit, "provenance": signature})
        fold_rows.append(metric_row)
        fold_audits.append(audit)
        print(
            f"LinXGBoost: fold {fold} RMSE={metric_row['RMSE']:.6f}; {audit['seconds']:.1f}s; {search.best_params_}",
            flush=True,
        )
        del search
        gc.collect()

    if not np.isfinite(oof).all():
        raise ValueError("Predicciones OOF incompletas.")
    fold_frame = pd.DataFrame(fold_rows).sort_values("Fold")
    fold_frame.to_csv(OUTPUT_DIR / "fold_metrics.csv", index=False, encoding="utf-8-sig")

    print("LinXGBoost: HPO final con todo train; el test permanece reservado.", flush=True)
    final_search = _new_search(train)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        with threadpool_limits(limits=1), joblib.parallel_backend("loky", inner_max_num_threads=1):
            final_search.fit(train[FEATURES], train[TARGET].to_numpy(dtype=np.float64), groups=train[GROUP])
    best_estimator = final_search.best_estimator_
    best_params = final_search.best_params_
    test_prediction = np.asarray(best_estimator.predict(test[FEATURES]), dtype=np.float64)
    if test_prediction.shape != (len(test),) or not np.isfinite(test_prediction).all():
        raise ValueError("Predicciones de test inválidas.")

    _search_table(final_search).to_csv(OUTPUT_DIR / "busqueda_final.csv", index=False, encoding="utf-8-sig")
    joblib.dump(best_estimator, OUTPUT_DIR / "modelo_final.joblib")
    fold_frame.to_csv(OUTPUT_DIR / "fold_metrics.csv", index=False, encoding="utf-8-sig")
    _save_oof(prediction_path, train, oof, pd.read_csv(E3_OUTPUT / "train.csv.gz")["fold"].to_numpy(dtype=int))
    pd.DataFrame({
        TARGET: test[TARGET].to_numpy(dtype=np.float64),
        e3_comparison.PERIOD: test[e3_comparison.PERIOD].to_numpy(),
        "prediction": test_prediction,
    }).to_csv(
        test_prediction_path, index=False, compression="gzip", float_format="%.17g"
    )

    cv_rows = []
    for name in ("RMSE", "MAE", "MAPE (%)", "R²"):
        values = fold_frame[name].to_numpy(dtype=float)
        cv_rows.append({
            "metrica": name,
            "media_cv": float(np.mean(values)),
            "sd_cv": float(np.std(values, ddof=0)),
            "OOF_agrupado": metrics(train[TARGET], oof)[name],
        })
    report = {
        "model": LABEL,
        "test": metrics(test[TARGET], test_prediction),
        "cv": cv_rows,
        "best_params": best_params,
        "trees_fitted_final": len(best_estimator.named_steps["modelo"].trees_),
        "inner_rmse_final": float(-final_search.best_score_),
        "fold_metrics": fold_frame.to_dict("records"),
        "fold_audit": fold_audits,
        "partition_audit": partition_audit,
        "implementation": _configuration(),
        "test_prediction_outside_grade_range": int(((test_prediction < 0.5) | (test_prediction > 5.0)).sum()),
        "test_used_for_selection": False,
        "provenance": signature,
    }
    write_json(report_path, report)
    print(json.dumps({"test": report["test"], "cv": cv_rows, "best_params": best_params}, ensure_ascii=False), flush=True)
    return report


def _reference_predictions(test):
    references = e3_comparison.reference_predictions(test)
    svr_path = e3_comparison._model_directory("svr_rbf") / "test_predictions.csv.gz"
    references["SVR RBF"] = e3_comparison._validate_reference_frame(
        pd.read_csv(svr_path), "SVR RBF", test
    )
    variant_paths = {
        "XGBoost ampliado (gbtree)": E3_OUTPUT / "xgboost_variantes" / "gbtree" / "test_predictions.csv.gz",
        "DART-XGBoost": E3_OUTPUT / "xgboost_variantes" / "dart" / "test_predictions.csv.gz",
        "DenseWeight-XGBoost": E3_OUTPUT / "xgboost_variantes" / "denseweight" / "test_predictions.csv.gz",
    }
    for name, path in variant_paths.items():
        references[name] = e3_comparison._validate_reference_frame(pd.read_csv(path), name, test)
    return references


def compare(train, test, signature, report):
    y = test[TARGET].to_numpy(dtype=np.float64)
    groups = test[GROUP].to_numpy()
    candidate_frame = pd.read_csv(OUTPUT_DIR / "test_predictions.csv.gz")
    candidate = e3_comparison._validate_reference_frame(candidate_frame, LABEL, test, "prediction")
    references = _reference_predictions(test)
    comparator_names = [
        "XGBoost",
        "SVR RBF",
        "TabICLv2",
        "SVM lineal",
        "XGBoost ampliado (gbtree)",
        "DART-XGBoost",
        "DenseWeight-XGBoost",
    ]

    contrast_rows, p_values = [], []
    for name in comparator_names:
        rows = e3_comparison.paired_comparison(y, candidate, references[name], groups)
        p_values.append(rows[0]["p_bilateral"])
        for row in rows:
            contrast_rows.append({"Modelo": LABEL, "Referencia": name, **row})
    adjusted = multipletests(p_values, method="holm")[1]
    for name, p_holm in zip(comparator_names, adjusted):
        for row in contrast_rows:
            if row["Referencia"] == name:
                row["p_Holm_family_7"] = float(p_holm) if row["p_bilateral"] is not None else None
                row["significativa_al_5%_Holm"] = bool(p_holm < 0.05) if row["p_bilateral"] is not None else False
    contrast_frame = pd.DataFrame(contrast_rows)
    contrast_frame.to_csv(OUTPUT_DIR / "contrastes_pareados.csv", index=False, encoding="utf-8-sig")

    reference_metrics = {name: metrics(y, references[name]) for name in comparator_names}
    candidate_metrics = report["test"]
    previous = pd.read_csv(E3_OUTPUT / "xgboost_variantes" / "ranking_global_25_modelos.csv")
    previous = previous.drop(columns=["rango_RMSE"], errors="ignore")
    p_by_reference = {name: float(p_values[i]) for i, name in enumerate(comparator_names)}
    holm_by_reference = {name: float(adjusted[i]) for i, name in enumerate(comparator_names)}
    xgb_metrics = reference_metrics["XGBoost"]
    svm_metrics = reference_metrics["SVM lineal"]
    new_row = {
        "Modelo": LABEL,
        "RMSE_test": candidate_metrics["RMSE"],
        "MAE_test": candidate_metrics["MAE"],
        "MAPE_test": candidate_metrics["MAPE (%)"],
        "R2_test": candidate_metrics["R²"],
        "p_bilateral": p_by_reference["SVM lineal"],
        "delta_RMSE_vs_SVM": candidate_metrics["RMSE"] - svm_metrics["RMSE"],
        "p_Holm_vs_SVM_21": np.nan,
        "p_Holm_global_55": np.nan,
        "delta_RMSE_vs_XGBoost": candidate_metrics["RMSE"] - xgb_metrics["RMSE"],
        "p_bilateral_vs_XGBoost": p_by_reference["XGBoost"],
        "p_Holm_variantes_12_vs_XGBoost": np.nan,
        "p_Holm_LinXGBoost_family_7_vs_XGBoost": holm_by_reference["XGBoost"],
        "familia_ajuste": "Holm7 LinXGBoost vs XGBoost, SVR RBF, TabICLv2, SVM y variantes XGBoost",
    }
    ranking = pd.concat([previous, pd.DataFrame([new_row])], ignore_index=True, sort=False)
    ranking = ranking.sort_values("RMSE_test").reset_index(drop=True)
    ranking.insert(0, "rango_RMSE", np.arange(1, len(ranking) + 1))
    ranking.to_csv(OUTPUT_DIR / "ranking_global_26_modelos.csv", index=False, encoding="utf-8-sig")

    candidate_metrics_table = pd.DataFrame([
        {"Modelo": name, **reference_metrics[name]} for name in comparator_names
    ] + [{"Modelo": LABEL, **candidate_metrics}])
    candidate_metrics_table["delta_RMSE_vs_XGBoost"] = candidate_metrics_table["RMSE"].map(
        lambda value: float(value - xgb_metrics["RMSE"])
    )
    candidate_metrics_table.to_csv(OUTPUT_DIR / "metricas_test_comparadores.csv", index=False, encoding="utf-8-sig")

    aggregate = {
        "model": report,
        "comparators": reference_metrics,
        "contrasts": contrast_frame.to_dict("records"),
        "holm_family_size": len(comparator_names),
        "ranking_global_26": ranking.to_dict("records"),
        "statistics": (
            "Permutación pareada por estudiante de SSE con 99.999 reasignaciones; "
            "IC95% bootstrap por estudiante con 10.000 réplicas; semilla 42. "
            "RMSE y R² comparten el contraste sobre SSE."
        ),
        "test_used_for_selection": False,
        "caveat": "Test temporal 202530 consultado en rondas anteriores; resultados exploratorios.",
        "provenance": signature,
    }
    write_json(OUTPUT_DIR / "reporte_comparativo.json", aggregate)
    _write_summary(report, reference_metrics, contrast_frame, ranking)
    print(ranking[["rango_RMSE", "Modelo", "RMSE_test", "delta_RMSE_vs_XGBoost"]].to_string(index=False), flush=True)
    return aggregate


def _write_summary(report, comparators, contrasts, ranking):
    lines = [
        "# LinXGBoost — Entregable 3",
        "",
        "Implementación independiente cotejada con el repositorio de [LinXGBoost (de Vito, 2017)](https://github.com/ldv1/LinXGBoost).",
        "Las hojas ajustan Ridge con las 67 columnas numéricas y one-hot, escaladas dentro de cada fit.",
        "Se alinea con el repositorio en la inicialización cero, profundidad raíz=1, poda, penalización lambda",
        "y aporte sin shrinkage del árbol final. Los cortes continuos se aproximan con 12 cuantiles; el",
        "repositorio barre todos los cortes distintos, así que esta es una aproximación de cómputo.",
        "Al puntuar cortes candidatos, este motor usa Ridge regularizado y `lstsq` si el solver falla; el",
        "repositorio además aplica un umbral explícito de condición y fallback constante por candidato.",
        "Se evalúa con GroupKFold anidado 5×5 y el test temporal se usa al final.",
        "El test ya se consultó en rondas anteriores, por lo que la comparación es exploratoria.",
        "El full-one-hot anterior (RMSE 1.012583) usaba convenciones distintas y queda supersedido.",
        "Una corrida previa de hojas solo numéricas obtuvo RMSE test 1.017309, pero usaba convenciones",
        "distintas de inicialización y shrinkage; está supersedida y no es una ablation comparable.",
        "Su reporte se conserva en `ablation_numeric_leaves/` por trazabilidad.",
        "",
        "## Resultado de LinXGBoost",
        "",
        "| Métrica | Test | CV media ± SD | OOF agrupado |",
        "|---|---:|---:|---:|",
    ]
    cv = {row["metrica"]: row for row in report["cv"]}
    for metric_name, test_key in (("RMSE", "RMSE"), ("MAE", "MAE"), ("MAPE (%)", "MAPE (%)"), ("R²", "R²")):
        item = cv[metric_name]
        lines.append(
            f"| {metric_name} | {report['test'][test_key]:.6f} | "
            f"{item['media_cv']:.6f} ± {item['sd_cv']:.6f} | {item['OOF_agrupado']:.6f} |"
        )
    lines += [
        "",
        "Parámetros finales seleccionados dentro de todo train: `" + json.dumps(report["best_params"], ensure_ascii=False) + "`.",
        "",
        "## Comparadores",
        "",
        "| Modelo | RMSE test | MAE | MAPE (%) | R² | ΔRMSE vs XGBoost |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, scores in comparators.items():
        lines.append(
            f"| {name} | {scores['RMSE']:.6f} | {scores['MAE']:.6f} | "
            f"{scores['MAPE (%)']:.4f} | {scores['R²']:.6f} | "
            f"{scores['RMSE'] - comparators['XGBoost']['RMSE']:+.6f} |"
        )
    scores = report["test"]
    lines.append(
        f"| {LABEL} | {scores['RMSE']:.6f} | {scores['MAE']:.6f} | {scores['MAPE (%)']:.4f} | "
        f"{scores['R²']:.6f} | {scores['RMSE'] - comparators['XGBoost']['RMSE']:+.6f} |"
    )
    rmse_rows = contrasts[contrasts["metrica"].eq("RMSE")]
    lines += [
        "",
        "## Contrastes pareados de RMSE",
        "",
        "Holm7 corrige los siete contrastes del nuevo candidato frente a XGBoost, SVR RBF, TabICLv2,",
        "SVM lineal y las tres variantes XGBoost. Las correcciones anteriores Holm55 y Holm12 se mantienen separadas.",
        "",
        "| Referencia | ΔRMSE | IC95% | p bruto | p Holm7 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rmse_rows.to_dict("records"):
        lines.append(
            f"| {row['Referencia']} | {row['diferencia_candidato_menos_referencia']:+.6f} | "
            f"[{row['IC_2.5%']:+.6f}, {row['IC_97.5%']:+.6f}] | "
            f"{row['p_bilateral']:.5f} | {row['p_Holm_family_7']:.5f} |"
        )
    lines += [
        "",
        "## Ranking RMSE de los 26 modelos",
        "",
        "El ranking es descriptivo. Los p-valores pertenecen a familias de contraste distintas y no se",
        "combinan como si formaran una sola corrección global.",
        "",
        "| Puesto | Modelo | RMSE test | ΔRMSE vs XGBoost |",
        "|---:|---|---:|---:|",
    ]
    for row in ranking.to_dict("records"):
        delta = row.get("delta_RMSE_vs_XGBoost")
        delta_text = f"{delta:+.6f}" if pd.notna(delta) else "—"
        lines.append(
            f"| {int(row['rango_RMSE'])} | {row['Modelo']} | {row['RMSE_test']:.6f} | {delta_text} |"
        )
    lines += [
        "",
        "Los resultados de CV, con parámetros elegidos de forma anidada, se leen junto con el test y los",
        "contrastes pareados; el test no se usa para elegir hiperparámetros.",
        "",
    ]
    (OUTPUT_DIR / "resumen.md").write_text("\n".join(lines), encoding="utf-8")


def run(force=False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train, test, fold_ids, folds, partition_audit = e3_comparison.canonical_partitions()
    signature = provenance()
    model_report = run_model(signature, train, test, folds, partition_audit, force=force)
    compare(train, test, signature, model_report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recalcular todos los folds y la selección final.")
    args = parser.parse_args()
    run(force=args.force)
