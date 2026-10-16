"""Evaluación anidada del checkpoint TabFM 1.0.0 en E3, con predicción CPU local."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import permutation_test
from sklearn.base import RegressorMixin, BaseEstimator
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from entregable3 import (BOOK, OUTPUT, FEATURES, GROUP, PERIOD, TARGET,
                         load_partitions, metrics, source_hashes, write_json)

KEY = "tabfm"
LABEL = "TabFM 1.0.0 (PyTorch CPU, 32 vistas)"
MODEL_DIR = BOOK / "modelos_preentrenados" / "tabfm_e3"
WEIGHTS_DIR = MODEL_DIR / "checkpoint"
WEIGHTS_REPO = "google/tabfm-1.0.0-pytorch"
WEIGHTS_REVISION = "77cb9cc1b4fd3a9c77fbb9552c218200bb4dab83"
WEIGHTS_FILE_SHA256 = "bd5a615b0322a8f04a895038de6df6fbd71430eca750e1d792f31048654674a9"
WEIGHTS_FILE_BYTES = 6591243724
OFFICIAL_CODE_COMMIT = "fbb665569425fd2f490c6576b3af967876fe11ff"
OUTLIER_THRESHOLD = 1e12  # Desactiva el recorte de extremos de TabFM para cumplir el protocolo E3.

_MODEL = None
_TORCH_THREADS_READY = False


def partitions():
    """Reutiliza los folds canónicos guardados, sin recalcularlos en sklearn1.6."""
    train, test, audit = load_partitions()
    if json.loads((OUTPUT / "modelos_lineales.json").read_text(encoding="utf-8"))["source_sha256"] != source_hashes():
        raise ValueError("La fuente E3 cambió respecto de los folds canónicos.")
    for frame, name in [(train, "train"), (test, "test")]:
        saved = pd.read_csv(OUTPUT / f"{name}.csv.gz")
        pd.testing.assert_frame_equal(
            frame[FEATURES + [TARGET, PERIOD]],
            saved[FEATURES + [TARGET, PERIOD]],
            check_dtype=False, check_exact=False,
        )
    saved_folds = pd.read_csv(OUTPUT / "train.csv.gz")["fold"].to_numpy(dtype=int)
    if len(saved_folds) != len(train) or set(np.unique(saved_folds)) != {1, 2, 3, 4, 5}:
        raise ValueError("Los cinco folds canónicos de train están incompletos.")
    folds = []
    for fold in range(1, 6):
        validation = np.flatnonzero(saved_folds == fold)
        fitting = np.flatnonzero(saved_folds != fold)
        shared = set(train.iloc[fitting][GROUP]) & set(train.iloc[validation][GROUP])
        if shared or not len(validation):
            raise ValueError(f"Fold canónico {fold} inválido: estudiantes compartidos o validación vacía.")
        folds.append((fitting, validation))
    if set(train[GROUP]) & set(test[GROUP]):
        raise ValueError("Hay estudiantes compartidos entre train y test temporal.")
    return train, test, folds, audit


def prepare_local_environment():
    """Aísla cache/telemetría antes de importar Hugging Face o TabFM."""
    os.environ["HF_HOME"] = str(MODEL_DIR / "hf_home")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_XET"] = "1"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_weights():
    """Descarga solo los pesos de regresión y fija el snapshot de Hugging Face."""
    prepare_local_environment()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import snapshot_download

    regression_dir = WEIGHTS_DIR / "regression"
    weight_file = regression_dir / "model.safetensors"
    weight_hash = sha256(weight_file) if weight_file.is_file() and weight_file.stat().st_size == WEIGHTS_FILE_BYTES else None
    valid_weight_file = (
        weight_file.is_file()
        and weight_file.stat().st_size == WEIGHTS_FILE_BYTES
        and weight_hash == WEIGHTS_FILE_SHA256
    )
    if not valid_weight_file:
        snapshot_download(
            repo_id=WEIGHTS_REPO,
            revision=WEIGHTS_REVISION,
            local_dir=str(WEIGHTS_DIR),
            allow_patterns=["regression/**", "README.md", "LICENSE*"],
            max_workers=1,
        )
    required = [regression_dir / "config.json"]
    if not regression_dir.is_dir() or not required[0].is_file():
        raise FileNotFoundError("No se descargó el directorio regression/config.json de TabFM.")
    if not weight_file.is_file() or weight_file.stat().st_size != WEIGHTS_FILE_BYTES:
        raise FileNotFoundError("El checkpoint de regresión está incompleto.")
    weight_hash = weight_hash or sha256(weight_file)
    if weight_hash != WEIGHTS_FILE_SHA256:
        raise ValueError("El checkpoint no coincide con el SHA-256 oficial de la revisión fijada.")
    files = {}
    for path in sorted(regression_dir.rglob("*")):
        if path.is_file() and ".cache" not in path.parts:
            key = str(path.relative_to(WEIGHTS_DIR)).replace("\\", "/")
            files[key] = weight_hash if path == weight_file else sha256(path)
    if len(files) < 2:
        raise FileNotFoundError("El snapshot de regresión de TabFM no contiene sus pesos completos.")
    manifest = {
        "repo_id": WEIGHTS_REPO,
        "revision": WEIGHTS_REVISION,
        "weights_size_bytes": WEIGHTS_FILE_BYTES,
        "model_type": "regression",
        "files_sha256": files,
        "weights_license": "tabfm-non-commercial-v1.0",
        "inference": "local CPU; no TabFM-Auto/LLM feature search",
    }
    write_json(MODEL_DIR / "procedencia_pesos.json", manifest)
    return manifest


def load_base_model():
    """Carga una sola copia in-context de pesos; fit() no optimiza parámetros."""
    global _MODEL, _TORCH_THREADS_READY
    if _MODEL is not None:
        return _MODEL
    prepare_local_environment()
    import torch
    from tabfm.src.pytorch import tabfm_v1_0_0 as tabfm_pytorch

    if not _TORCH_THREADS_READY:
        torch.set_num_threads(4)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        _TORCH_THREADS_READY = True
    if not (WEIGHTS_DIR / "regression" / "config.json").is_file():
        ensure_weights()
    _MODEL = tabfm_pytorch.load(
        model_type="regression",
        checkpoint_path=str(WEIGHTS_DIR),
        device="cpu",
        dtype=torch.bfloat16,
        use_cache=True,
    )
    return _MODEL


class TabFME3Regressor(RegressorMixin, BaseEstimator):
    """Adaptador E3 sobre el estimador oficial; mantiene las 15 columnas mixtas."""

    def __init__(self, n_estimators=32, random_state=42):
        self.n_estimators = n_estimators
        self.random_state = random_state

    def fit(self, X, y):
        prepare_local_environment()
        from tabfm import TabFMRegressor

        self.model_ = TabFMRegressor(
            model=load_base_model(),
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            max_num_rows=None,
            outlier_threshold=OUTLIER_THRESHOLD,
            enable_nnls=False,
            batch_size=1,
            cache_context=False,
        )
        self.model_.fit(X, y)
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        values = np.asarray(self.model_.predict(X), dtype=float)
        if values.shape != (len(X),) or not np.isfinite(values).all():
            raise ValueError("TabFM produjo predicciones inválidas.")
        return values


def provenance(weight_manifest):
    package_versions = {
        name: importlib.metadata.version(name)
        for name in ["tabfm", "torch", "numpy", "pandas", "scikit-learn",
                     "scipy", "statsmodels", "huggingface-hub"]
    }
    paths = [
        "evaluacion_nuevos_e3.py",
        "resultados/e3/train.csv.gz",
        "resultados/e3/test.csv.gz",
        "resultados/e3/clasicos/test_predictions.csv.gz",
        "resultados/e3/resumen_completo/modelos.csv",
        "resultados/e3/scopus/contrastes_pareados.csv",
    ]
    return {
        **source_hashes(),
        "evaluar_tabfm_e3.py": sha256(BOOK / "evaluar_tabfm_e3.py"),
        "requirements_tabfm_e3.txt": sha256(BOOK / "requirements_tabfm_e3.txt"),
        "experiment_inputs_sha256": {path: sha256(BOOK / path) for path in paths},
        "official_tabfm_code_commit": OFFICIAL_CODE_COMMIT,
        "weights": weight_manifest,
        "versions": package_versions,
        "configuration": {
            "n_estimators": 32,
            "normalization": ["none", "power"],
            "max_num_rows": None,
            "outlier_threshold": OUTLIER_THRESHOLD,
            "enable_nnls": False,
            "device": "cpu",
            "dtype": "bfloat16",
            "seed": 42,
        },
    }


def validate_classic_baseline():
    """Verifica la procedencia del XGBoost guardado sin instalarlo en este venv."""
    report = json.loads((OUTPUT / "clasicos" / "comparacion.json").read_text(encoding="utf-8"))
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
        raise ValueError("La evaluación clásica/XGBoost no corresponde a la fuente E3 actual.")
    return pd.read_csv(OUTPUT / "clasicos" / "test_predictions.csv.gz")


def paired_comparison(y, new, old, groups, seed=42):
    """Contraste SSE pareado por estudiante y bootstrap de RMSE/R², igual a E3."""
    codes, ids = pd.factorize(groups, sort=False)
    aggregate = lambda values: np.bincount(codes, weights=values, minlength=len(ids))
    new_sse, old_sse = aggregate((y - new) ** 2), aggregate((y - old) ** 2)
    test = permutation_test(
        (new_sse - old_sse,), lambda values, axis: values.sum(axis=axis),
        permutation_type="samples", vectorized=True, n_resamples=99999,
        batch=512, alternative="two-sided", rng=np.random.default_rng(seed),
    )
    n, sum_y, sum_y2 = aggregate(np.ones(len(y))), aggregate(y), aggregate(y * y)
    rng = np.random.default_rng(seed)
    rmse_delta, r2_delta = [], []
    for start in range(0, 10000, 512):
        batch = min(512, 10000 - start)
        ix = rng.integers(len(ids), size=(batch, len(ids)))
        count = n[ix].sum(axis=1)
        sse_new, sse_old = new_sse[ix].sum(axis=1), old_sse[ix].sum(axis=1)
        sst = sum_y2[ix].sum(axis=1) - sum_y[ix].sum(axis=1) ** 2 / count
        if (sst <= 0).any():
            raise ValueError("Varianza nula en el bootstrap por estudiante.")
        rmse_delta.extend(np.sqrt(sse_new / count) - np.sqrt(sse_old / count))
        r2_delta.extend((sse_old - sse_new) / sst)
    new_metrics, old_metrics = metrics(y, new), metrics(y, old)
    return [
        {
            "metrica": metric,
            "diferencia_TabFM_menos_referencia": new_metrics[metric] - old_metrics[metric],
            "IC_2.5%": float(np.quantile(draws, 0.025)),
            "IC_97.5%": float(np.quantile(draws, 0.975)),
            "p_bilateral": float(test.pvalue),
        }
        for metric, draws in [("RMSE", rmse_delta), ("R²", r2_delta)]
    ]


def _write_progress(folder, rows, audits, signature):
    write_json(folder / "progreso.json", {"folds": rows, "audit": audits, "provenance": signature})


def _recover_legacy_completed_folds(folder, train, folds, signature):
    """Valida y migra checkpoints completos creados cuando provenance devolvía None."""
    progress_path = folder / "progreso.json"
    if not progress_path.is_file():
        return False
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    if progress.get("provenance") is not None:
        return False
    if len(progress.get("folds", [])) != len(folds) or len(progress.get("audit", [])) != len(folds):
        return False

    recovery_note = (
        "Procedencia reconstruida tras validar las predicciones, métricas, filas y folds "
        "del checkpoint legado; el registro original tenía provenance=null."
    )
    recovered = []
    expected_oof = np.full(len(train), np.nan, dtype=float)

    for k, (fit_idx, val_idx) in enumerate(folds, 1):
        checkpoint_path = folder / f"externo_{k}.json"
        pred_path = folder / f"oof_{k}.csv.gz"
        if not checkpoint_path.is_file() or not pred_path.is_file():
            return False
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("provenance") is not None:
            return False
        saved = pd.read_csv(pred_path)
        required = {"fila_fuente", PERIOD, TARGET, "fold", "prediccion", "residuo"}
        if not required.issubset(saved.columns) or len(saved) != len(val_idx):
            return False
        expected_frame = train.iloc[val_idx]
        if (not np.array_equal(saved["fila_fuente"], expected_frame["fila_fuente"])
                or not np.array_equal(saved["fold"], np.full(len(val_idx), k))
                or not np.array_equal(saved[PERIOD], expected_frame[PERIOD])
                or not np.array_equal(saved[TARGET], expected_frame[TARGET])):
            return False
        prediction = saved["prediccion"].to_numpy(float)
        if not np.isfinite(prediction).all():
            return False
        if not np.allclose(saved["residuo"], expected_frame[TARGET].to_numpy(float) - prediction,
                           rtol=0, atol=1e-12):
            return False

        metric_row = checkpoint.get("metrics", {})
        audit_row = checkpoint.get("audit", {})
        if metric_row != progress["folds"][k - 1] or audit_row != progress["audit"][k - 1]:
            return False
        if metric_row.get("Modelo") != LABEL or metric_row.get("Fold") != k:
            return False
        recomputed = metrics(expected_frame[TARGET], prediction)
        for name, value in recomputed.items():
            if not np.isclose(metric_row.get(name, np.nan), value, rtol=0, atol=1e-12):
                return False

        fit_frame = train.iloc[fit_idx]
        if (audit_row.get("fit_rows") != len(fit_idx)
                or audit_row.get("validation_rows") != len(val_idx)
                or audit_row.get("fit_students") != fit_frame[GROUP].nunique()
                or audit_row.get("validation_students") != expected_frame[GROUP].nunique()
                or audit_row.get("shared_students") != 0
                or audit_row.get("rows_in_context") != len(fit_idx)
                or audit_row.get("best_params") != {"n_estimators": 32, "random_state": 42}
                or not isinstance(audit_row.get("seconds"), (int, float))
                or audit_row["seconds"] <= 0):
            return False
        expected_oof[val_idx] = prediction
        recovered.append((checkpoint_path, checkpoint))

    if not np.isfinite(expected_oof).all():
        return False
    train_path = folder / "train_predictions.csv.gz"
    if not train_path.is_file():
        return False
    saved_train = pd.read_csv(train_path)
    expected_fold_ids = pd.read_csv(OUTPUT / "train.csv.gz")["fold"].to_numpy()
    if (len(saved_train) != len(train)
            or not np.array_equal(saved_train["fila_fuente"], train["fila_fuente"])
            or not np.array_equal(saved_train["fold"], expected_fold_ids)
            or not np.allclose(saved_train["prediccion"], expected_oof, rtol=0, atol=1e-12)):
        return False

    for checkpoint_path, checkpoint in recovered:
        checkpoint["provenance"] = signature
        checkpoint["provenance_recovery"] = recovery_note
        write_json(checkpoint_path, checkpoint)
    progress["provenance"] = signature
    progress["provenance_recovery"] = recovery_note
    write_json(progress_path, progress)
    print("TabFM: cinco folds existentes validados y recuperados; se continuará con el ajuste final.", flush=True)
    return True


def run(force=False):
    train, test, folds, audit = partitions()
    classic = validate_classic_baseline()
    if len(classic) != len(test) or "xgboost" not in classic:
        raise ValueError("Las predicciones XGBoost guardadas no coinciden con test 202530.")
    weight_manifest = ensure_weights()
    signature = provenance(weight_manifest)
    folder = OUTPUT / "tabfm"
    folder.mkdir(parents=True, exist_ok=True)
    report_path = folder / "reporte.json"
    if report_path.exists() and not force:
        cached = json.loads(report_path.read_text(encoding="utf-8"))
        if cached.get("provenance") == signature:
            print("TabFM: resultados completos con procedencia verificada; usa --force para repetir.", flush=True)
            return cached
    if not force:
        progress_path = folder / "progreso.json"
        if progress_path.is_file():
            saved_progress = json.loads(progress_path.read_text(encoding="utf-8"))
            if saved_progress.get("provenance") is None:
                if not _recover_legacy_completed_folds(folder, train, folds, signature):
                    raise RuntimeError(
                        "Los checkpoints TabFM heredados no pasaron la validación; "
                        "se detuvo antes de repetir folds. Revisa resultados/e3/tabfm/."
                    )

    oof = np.full(len(train), np.nan, dtype=float)
    rows, audits = [], []
    for k, (fit_idx, val_idx) in enumerate(folds, 1):
        checkpoint_path = folder / f"externo_{k}.json"
        pred_path = folder / f"oof_{k}.csv.gz"
        if checkpoint_path.exists() and pred_path.exists() and not force:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint.get("provenance") == signature:
                saved = pd.read_csv(pred_path)
                np.testing.assert_array_equal(saved["fila_fuente"], train.iloc[val_idx]["fila_fuente"])
                oof[val_idx] = saved["prediccion"].to_numpy(float)
                rows.append(checkpoint["metrics"])
                audits.append(checkpoint["audit"])
                continue
        fit_frame, val_frame = train.iloc[fit_idx], train.iloc[val_idx]
        start = time.perf_counter()
        print(f"TabFM: fold externo {k}/5, fit={len(fit_idx)}, validación={len(val_idx)}", flush=True)
        estimator = TabFME3Regressor(n_estimators=32, random_state=42)
        with warnings.catch_warnings(), threadpool_limits(limits=1):
            warnings.filterwarnings("ignore", message="Found unknown categories")
            estimator.fit(fit_frame[FEATURES], fit_frame[TARGET].to_numpy(float))
            prediction = estimator.predict(val_frame[FEATURES])
        oof[val_idx] = prediction
        metric_row = {"Modelo": LABEL, "Fold": k, **metrics(val_frame[TARGET], prediction)}
        audit_row = {
            "fold": k,
            "fit_rows": len(fit_idx),
            "validation_rows": len(val_idx),
            "fit_students": int(fit_frame[GROUP].nunique()),
            "validation_students": int(val_frame[GROUP].nunique()),
            "shared_students": int(len(set(fit_frame[GROUP]) & set(val_frame[GROUP]))),
            "rows_in_context": len(fit_frame),
            "best_params": {"n_estimators": 32, "random_state": 42},
            "seconds": time.perf_counter() - start,
        }
        export = val_frame[["fila_fuente", PERIOD, TARGET]].copy()
        export["fold"] = k
        export["prediccion"] = prediction
        export["residuo"] = export[TARGET] - prediction
        export.to_csv(pred_path, index=False, compression="gzip")
        write_json(checkpoint_path, {"metrics": metric_row, "audit": audit_row, "provenance": signature})
        rows.append(metric_row)
        audits.append(audit_row)
        _write_progress(folder, rows, audits, signature)
        print(f"TabFM: fold {k} RMSE={metric_row['RMSE']:.6f}, {audit_row['seconds']:.1f}s", flush=True)
        del estimator
        gc.collect()

    if not np.isfinite(oof).all():
        raise ValueError("Predicciones OOF incompletas.")
    fold_frame = pd.DataFrame(rows).sort_values("Fold")
    fold_frame.to_csv(folder / "fold_metrics.csv", index=False, encoding="utf-8-sig")
    train_export = train[["fila_fuente", PERIOD, TARGET]].copy()
    train_export["fold"] = pd.read_csv(OUTPUT / "train.csv.gz")["fold"].to_numpy()
    train_export["prediccion"] = oof
    train_export["residuo"] = train_export[TARGET] - oof
    train_export.to_csv(folder / "train_predictions.csv.gz", index=False, compression="gzip")

    # Los hiperparámetros/configuración quedaron fijados antes del primer test.
    write_json(folder / "seleccion_antes_test.json", {
        "configuration": signature["configuration"],
        "test_used": False,
        "selection": "TabFM zero-shot; sin fine-tuning ni búsqueda de hiperparámetros",
        "cv_outer_rmse_mean": float(fold_frame["RMSE"].mean()),
    })
    print("TabFM: fit final sobre train completo; primer acceso predictivo a test 202530.", flush=True)
    final_estimator = TabFME3Regressor(n_estimators=32, random_state=42)
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings("ignore", message="Found unknown categories")
        final_estimator.fit(train[FEATURES], train[TARGET].to_numpy(float))
        test_prediction = final_estimator.predict(test[FEATURES])
    test_score = metrics(test[TARGET], test_prediction)
    test_export = test[["fila_fuente", PERIOD, TARGET]].copy()
    test_export["prediccion"] = test_prediction
    test_export["residuo"] = test_export[TARGET] - test_prediction
    test_export.to_csv(folder / "test_predictions.csv.gz", index=False, compression="gzip")

    svm = pd.read_csv(OUTPUT / "test.csv.gz")["svm"].to_numpy(float)
    xgb = classic["xgboost"].to_numpy(float)
    y = test[TARGET].to_numpy(float)
    comparisons = []
    for reference, prediction in [("SVM lineal", svm), ("XGBoost", xgb)]:
        comparisons.append({
            "referencia": reference,
            "rows": paired_comparison(y, test_prediction, prediction, test[GROUP]),
        })

    previous = pd.read_csv(OUTPUT / "resumen_completo" / "modelos.csv")
    previous_svm_p = previous["p_bilateral"].dropna().to_numpy(float)
    prior_scopus = pd.read_csv(OUTPUT / "scopus" / "contrastes_pareados.csv")
    prior_xgb_p = prior_scopus.loc[
        prior_scopus["Referencia"].eq("XGBoost") & prior_scopus["metrica"].eq("RMSE"),
        "p_bilateral",
    ].to_numpy(float)
    current_p = np.asarray([comparison["rows"][0]["p_bilateral"] for comparison in comparisons])
    if len(previous_svm_p) != 17 or len(prior_xgb_p) != 4 or len(current_p) != 2:
        raise ValueError("No coincide la familia histórica predeclarada de 23 contrastes.")
    holm_18_svm = multipletests(np.r_[previous_svm_p, current_p[0]], method="holm")[1]
    holm_23 = multipletests(np.r_[previous_svm_p, prior_xgb_p, current_p], method="holm")[1]
    comparisons[0]["p_Holm_18_vs_SVM"] = float(holm_18_svm[-1])
    for comparison, p in zip(comparisons, holm_23[-2:]):
        comparison["p_Holm_global_23"] = float(p)
        for metric_row in comparison["rows"]:
            metric_row["p_Holm_global_23"] = float(p)
            metric_row["significativa_al_5%_Holm"] = bool(p < 0.05)

    ranking = previous[["Modelo", "RMSE_test", "p_bilateral", "p_Holm_global_21"]].copy()
    ranking = pd.concat([ranking, pd.DataFrame([{
        "Modelo": LABEL,
        "RMSE_test": test_score["RMSE"],
        "p_bilateral": comparisons[0]["rows"][0]["p_bilateral"],
        "p_Holm_global_21": np.nan,
    }])], ignore_index=True)
    ranking["delta_RMSE_vs_SVM"] = ranking["RMSE_test"] - metrics(y, svm)["RMSE"]
    ranking["p_Holm_18_vs_SVM"] = np.nan
    ranking.loc[ranking.Modelo.ne("SVM lineal"), "p_Holm_18_vs_SVM"] = holm_18_svm
    ranking["p_Holm_global_23"] = np.nan
    if len(ranking) != 19:
        raise ValueError("El ranking debe contener los 18 métodos previos y TabFM.")
    ranking.loc[ranking.Modelo.ne("SVM lineal"), "p_Holm_global_23"] = np.r_[holm_23[:17], holm_23[-2]]
    ranking = ranking.sort_values("RMSE_test").reset_index(drop=True)
    ranking.to_csv(folder / "comparacion_rmse_test.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([
        {"referencia": comparison["referencia"], **row}
        for comparison in comparisons for row in comparison["rows"]
    ]).to_csv(folder / "contrastes_pareados.csv", index=False, encoding="utf-8-sig")

    report = {
        "model": LABEL,
        "key": KEY,
        "test": test_score,
        "cv": [
            {"metrica": metric, "media_cv": float(fold_frame[metric].mean()),
             "sd_cv": float(fold_frame[metric].std(ddof=0)),
             "OOF_agrupado": metrics(train[TARGET], oof)[metric]}
            for metric in test_score
        ],
        "fold_audit": audits,
        "partition": audit,
        "provenance": signature,
        "features": FEATURES,
        "target": TARGET,
        "paired_comparisons": comparisons,
        "family_size_vs_svm": 18,
        "family_size_global": 23,
        "test_used_for_selection": False,
        "method": "GroupKFold externo 5 por estudiante; TabFM fijo zero-shot, sin ajuste de pesos ni HPO; test temporal 202530 al final.",
        "fold_source": "resultados/e3/train.csv.gz; folds canónicos de sklearn 1.9.1 reutilizados para preservar particiones al usar sklearn 1.6.0 en venv_tabfm",
        "limitations": [
            "El test temporal ha sido consultado en experimentos previos; la inferencia es exploratoria.",
            "Los pesos preentrenados usan licencia no comercial.",
            "Se desactivó el recorte de extremos propio del preprocesador TabFM para conservar outliers E3.",
        ],
    }
    write_json(report_path, report)
    summary = [
        "# TabFM en E3",
        "",
        "TabFM v1.0.0, checkpoint de regresión de Google, inferencia CPU local; no se ajustaron sus pesos.",
        "Mismas variables, limpieza, grupos y test temporal E3. La selección es fija: no hay tuning.",
        "Se conserva el test hasta completar los cinco folds externos y ajustar el estimador final.",
        "",
        "## Validación agrupada",
        "",
        "| Métrica | Media 5 folds | SD | OOF agrupado | Test temporal |",
        "|---|---:|---:|---:|---:|",
    ]
    cv_by_metric = {row["metrica"]: row for row in report["cv"]}
    for metric in test_score:
        item = cv_by_metric[metric]
        summary.append(
            f"| {metric} | {item['media_cv']:.6f} | {item['sd_cv']:.6f} | "
            f"{item['OOF_agrupado']:.6f} | {test_score[metric]:.6f} |"
        )
    summary.extend(["", "## Contrastes pareados", "",
                    "Permutación por estudiante: 99.999 reasignaciones; bootstrap: 10.000; semilla 42.",
                    "Holm global 23: 17 pares históricos vs. SVM, 4 previos vs. XGBoost y 2 de TabFM.",
                    "RMSE y R² comparten el contraste SSE y no se cuentan como hipótesis distintas.", "",
                    "| Referencia | Δ RMSE | IC95% marginal | p bilateral | p Holm global23 |",
                    "|---|---:|---:|---:|---:|"])
    for comparison in comparisons:
        row = comparison["rows"][0]
        summary.append(
            f"| {comparison['referencia']} | {row['diferencia_TabFM_menos_referencia']:+.6f} | "
            f"[{row['IC_2.5%']:+.6f}, {row['IC_97.5%']:+.6f}] | "
            f"{row['p_bilateral']:.5f} | {row['p_Holm_global_23']:.5f} |"
        )
    summary.extend(["", "Los IC son marginales. La comparación temporal es exploratoria por reutilización del test.",
                    "No rechazar H0 no demuestra equivalencia; una cohorte futura reservada daría una confirmación independiente."])
    (folder / "resumen.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({"test": test_score, "cv": report["cv"], "comparisons": comparisons}, ensure_ascii=False), flush=True)
    del final_estimator
    gc.collect()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recalcular todos los folds y el test final.")
    args = parser.parse_args()
    run(force=args.force)
