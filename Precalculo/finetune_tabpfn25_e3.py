r"""Fine-tuning LOCAL de TabPFN 2.5 para E3. La ejecución la inicia el usuario.

Desde la raíz del proyecto:
  Precalculo\venv\Scripts\python.exe Precalculo/finetune_tabpfn25_e3.py --check-only
  Precalculo\venv\Scripts\python.exe Precalculo/finetune_tabpfn25_e3.py

Usa el SDK 6.4.1 instalado y sus utilidades de fine-tuning, con episodios por
estudiante propios para evitar el split aleatorio por filas del wrapper estándar.
Referencia: https://github.com/PriorLabs/TabPFN/tree/v6.4.1/src/tabpfn/finetuning
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import logging
import random
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from entregable3 import (BOOK, FEATURES, GROUP, TARGET, make_pipeline, metrics,
                        source_hashes, write_json)
from evaluacion_nuevos_e3 import (CHECKPOINT, MODEL_DIR, partitions,
                                 prepare_tabpfn_environment)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grouped_episodes(groups, max_rows, seed):
    """Cada fila participa una vez por época; los grupos nunca se fragmentan.

    max_rows es un límite orientativo de memoria: se permite excederlo para
    conservar un grupo o fusionar el último episodio si tiene un solo grupo.
    """
    groups = np.asarray(groups)
    ids = np.random.default_rng(seed).permutation(pd.unique(groups))
    if len(ids) < 2:
        raise ValueError('Se requieren al menos dos estudiantes para contexto/query.')
    result, current, count = [], [], 0
    for group in ids:
        ix = np.flatnonzero(groups == group)
        if len(current) >= 2 and count + len(ix) > max_rows:
            result.append(np.concatenate(current))
            current, count = [], 0
        current.append(ix)
        count += len(ix)
    if len(current) == 1 and result:
        result[-1] = np.concatenate([result[-1], *current])
    else:
        result.append(np.concatenate(current))
    np.testing.assert_array_equal(np.sort(np.concatenate(result)), np.arange(len(groups)))
    return result


def context_query_split(groups, seed, query_ratio=.2):
    groups = np.asarray(groups)
    context, query = next(GroupShuffleSplit(n_splits=1, test_size=query_ratio,
                                            random_state=seed).split(np.zeros(len(groups)), groups=groups))
    if set(groups[context]) & set(groups[query]):
        raise AssertionError('Un estudiante aparece en contexto y query.')
    return context, query


def preflight(args):
    prepare_tabpfn_environment()  # Antes de importar TabPFN: sin telemetría.
    if importlib.metadata.version('tabpfn') != '6.4.1':
        raise RuntimeError('Este script requiere tabpfn==6.4.1; usa requirements_tabpfn25.txt.')
    import torch
    from tabpfn.finetuning.finetuned_regressor import FinetunedTabPFNRegressor
    from tabpfn.finetuning.data_util import get_preprocessed_dataset_chunks, meta_dataset_collator
    from tabpfn.model_loading import save_tabpfn_model
    path = MODEL_DIR / CHECKPOINT
    if not path.is_file():
        raise FileNotFoundError('Faltan pesos base. Ejecuta primero Precalculo/descargar_tabpfn25.py.')
    manifest = json.loads((MODEL_DIR / 'procedencia.json').read_text(encoding='utf-8'))
    if manifest['filename'] != CHECKPOINT or sha256(path) != manifest['sha256']:
        raise ValueError('Los pesos no coinciden con el checkpoint oficial TabPFN 2.5 registrado.')
    device = ('cuda' if torch.cuda.is_available() else 'cpu') if args.device == 'auto' else args.device
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA no está disponible en este venv/equipo. Usa --device cpu.')
    if args.epochs < 1 or args.patience < 1 or args.episode_rows < 8:
        raise ValueError('epochs/patience deben ser positivos y episode-rows >= 8.')
    if not 0 < args.query_ratio < 1 or args.learning_rate <= 0 or args.weight_decay < 0 or args.min_delta < 0:
        raise ValueError('query-ratio debe estar entre 0 y 1; revisar learning-rate/weight-decay.')
    if min(args.train_estimators, args.eval_estimators, args.threads) < 1:
        raise ValueError('Estimadores e hilos deben ser positivos.')
    train, test, folds, audit = partitions()
    for k, (fi, va) in enumerate(folds, 1):
        assert not set(train.iloc[fi][GROUP]) & set(train.iloc[va][GROUP])
        for ix in grouped_episodes(train.iloc[fi][GROUP].to_numpy(), args.episode_rows, args.seed+k):
            context_query_split(train.iloc[fi][GROUP].to_numpy()[ix], args.seed+k, args.query_ratio)
    return path, device, train, test, folds, audit


def native_save(model, path, epoch):
    """Checkpoint nativo recargable con TabPFNRegressor(model_path=...)."""
    from tabpfn.model_loading import save_tabpfn_model
    path = Path(path)
    temporary = path.with_suffix('.partial')
    save_tabpfn_model(model, temporary, additional_fields={'epoch': epoch, 'e3_finetuned': True})
    temporary.replace(path)


def new_training_model(base_path, args, device, seed):
    import torch
    from tabpfn import TabPFNRegressor
    from tabpfn.finetuning.finetuned_regressor import FinetunedTabPFNRegressor
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if device == 'cuda':
        torch.cuda.manual_seed_all(seed)
    model = TabPFNRegressor(model_path=str(base_path), device=device,
                            n_estimators=args.train_estimators, random_state=seed,
                            categorical_features_indices=[], n_preprocessing_jobs=1,
                            inference_precision=torch.float32, fit_mode='batched',
                            ignore_pretraining_limits=True, memory_saving_mode=False,
                            inference_config={'SUBSAMPLE_SAMPLES': None, 'OUTLIER_REMOVAL_STD': None})
    model._initialize_model_variables()
    model.model_.to(device)
    # El SDK oficial usa esta opción para recomputar activaciones en backward.
    model.model_.recompute_layer = True
    for parameter in model.model_.parameters():
        parameter.requires_grad_(True)
    loss_helper = FinetunedTabPFNRegressor(device=device,
        n_estimators_finetune=args.train_estimators, crps_loss_weight=1., mse_loss_weight=1.,
        ce_loss_weight=0., crls_loss_weight=0., mae_loss_weight=0.)
    loss_helper.finetuned_estimator_ = model
    optimizer = torch.optim.AdamW(model.model_.parameters(), lr=args.learning_rate,
                                   weight_decay=args.weight_decay)
    return model, loss_helper, optimizer


def train_epoch(model, loss_helper, optimizer, X, y, groups, args, seed):
    """Backprop real con pérdida CRPS + MSE del SDK; sin usar validación/test."""
    import torch
    from tabpfn.finetuning.data_util import get_preprocessed_dataset_chunks, meta_dataset_collator
    from tabpfn.finetuning._torch_compat import sdpa_kernel_context
    model.model_.train()
    losses, n_steps = [], 0
    for batch_number, ix in enumerate(grouped_episodes(groups, args.episode_rows, seed)):
        local_groups = np.asarray(groups)[ix]
        context, query = context_query_split(local_groups, seed+batch_number, args.query_ratio)

        def split_fn(xx, yy, stratify=None):
            # El SDK conserva el orden de filas cuando max_data_size=None.
            if len(xx) != len(ix):
                raise AssertionError('El SDK cambió el orden/tamaño del episodio.')
            return xx[context], xx[query], yy[context], yy[query]

        dataset = get_preprocessed_dataset_chunks(calling_instance=model,
            X_raw=X[ix], y_raw=y[ix], split_fn=split_fn, max_data_size=None,
            model_type='regressor', equal_split_size=False, seed=seed+batch_number,
            shuffle=False)
        batch = meta_dataset_collator([dataset[0]])
        loss_helper._setup_batch(batch)
        model.fit_from_preprocessed(batch.X_context, batch.y_context, batch.cat_indices, batch.configs)
        optimizer.zero_grad(set_to_none=True)
        # Float32 también en CUDA: evita requerir AMP/GradScaler para ejecutar el script.
        with sdpa_kernel_context():
            loss = loss_helper._forward_with_loss(batch)
        if not torch.isfinite(loss):
            raise FloatingPointError('Pérdida no finita; ejecución detenida sin sustituir pesos.')
        with sdpa_kernel_context():
            loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.model_.parameters(), 1., error_if_nonfinite=True)
        if not any(p.grad is not None for p in model.model_.parameters()):
            raise RuntimeError('No se produjeron gradientes: el fine-tuning no se ejecutó.')
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
        n_steps += 1
        logging.info('  episodio %d: contexto=%d query=%d loss=%.6f grad_norm=%.6f',
                     batch_number+1, len(context), len(query), losses[-1], float(grad_norm))
        del batch, dataset, loss
    return float(np.mean(losses)), n_steps


def predict_checkpoint(path, X_context, y_context, X_predict, args, device):
    import torch
    from tabpfn import TabPFNRegressor
    model = TabPFNRegressor(model_path=str(path), device=device, n_estimators=args.eval_estimators,
        random_state=args.seed, n_preprocessing_jobs=1, categorical_features_indices=[],
        fit_mode='low_memory', memory_saving_mode=True, ignore_pretraining_limits=True,
        inference_config={'SUBSAMPLE_SAMPLES': None, 'OUTLIER_REMOVAL_STD': None})
    model.fit(X_context, y_context)
    pred = np.asarray(model.predict(X_predict), dtype=float)
    del model
    gc.collect()
    if device == 'cuda':
        torch.cuda.empty_cache()
    return pred


def fine_tune(args):
    base, device, train, test, folds, audit = preflight(args)
    print(f'Validado: TabPFN 2.5, dispositivo={device}, train={len(train)}, test reservado={len(test)}', flush=True)
    if args.check_only:
        print('Comprobación terminada: dependencias, pesos, variables y particiones válidas. Sin entrenar ni crear pesos.')
        return
    import torch
    torch.set_num_threads(args.threads)
    output = Path(args.output_dir).expanduser().resolve() if args.output_dir else (
        MODEL_DIR / 'finetuning' / datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    # Nunca sobrescribir pesos/ejecuciones existentes, incluyendo el checkpoint base.
    output.mkdir(parents=True, exist_ok=False)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(output/'entrenamiento.log', encoding='utf-8')],
                        force=True)
    versions = {p: importlib.metadata.version(p) for p in
                ['tabpfn', 'torch', 'numpy', 'pandas', 'scikit-learn', 'scipy']}
    metadata = {'status': 'running', 'arguments': vars(args), 'device': device,
                'versions': versions, 'partition': audit, 'features': FEATURES, 'target': TARGET,
                'base_checkpoint': str(base), 'base_sha256': sha256(base),
                'source_sha256': {**source_hashes(), 'finetune_tabpfn25_e3.py': sha256(__file__)},
                'method': 'Selección de épocas en 5 folds por estudiante de train; '
                          'reentrenamiento final desde pesos base con todo train. '
                          'La CV usada para seleccionar NO es una evaluación externa anidada.',
                'loss': 'CRPS + MSE de la media, ambos peso 1; AdamW, float32, grad_clip=1',
                'test_used_for_selection': False}
    write_json(output/'ejecucion.json', metadata)
    logging.info('Salida local: %s', output)
    if device == 'cpu':
        logging.info('CPU: el fine-tuning puede tardar horas; --episode-rows controla memoria de activaciones.')
    records, choices, selection_summary = [], [], []
    try:
        for fold, (fi, va) in enumerate(folds, 1):
            folder = output/f'seleccion_fold_{fold}'
            folder.mkdir()
            fit, val = train.iloc[fi], train.iloc[va]
            prep = clone(make_pipeline().named_steps['preprocesamiento'])
            X = prep.fit_transform(fit[FEATURES])
            V = prep.transform(val[FEATURES])
            y, vy, groups = fit[TARGET].to_numpy(float), val[TARGET].to_numpy(float), fit[GROUP].to_numpy()
            baseline = metrics(vy, predict_checkpoint(base, X, y, V, args, device))
            model, loss_helper, optimizer = new_training_model(base, args, device, args.seed+fold)
            best_rmse, best_epoch, best_scores, stale = np.inf, 0, None, 0
            for epoch in range(1, args.epochs+1):
                loss, steps = train_epoch(model, loss_helper, optimizer, X, y, groups,
                                          args, args.seed+1000*fold+epoch)
                last = folder/'ultimo.ckpt'
                native_save(model, last, epoch)
                score = metrics(vy, predict_checkpoint(last, X, y, V, args, device))
                records.append({'fold': fold, 'epoch': epoch, 'loss': loss, 'optimizer_steps': steps, **score})
                if score['RMSE'] < best_rmse-args.min_delta:
                    best_rmse, best_epoch, best_scores, stale = score['RMSE'], epoch, score, 0
                    native_save(model, folder/'mejor.ckpt', epoch)
                else:
                    stale += 1
                pd.DataFrame(records).to_csv(output/'seleccion_epocas.csv', index=False)
                logging.info('Fold %d/5 época %d: RMSE=%.6f mejor=%d', fold, epoch, score['RMSE'], best_epoch)
                if stale >= args.patience:
                    break
            choices.append(best_epoch)
            selection_summary.append({'fold': fold, 'best_epoch': best_epoch,
                                       'base_validation': baseline, 'finetuned_validation': best_scores})
            write_json(output/'seleccion.json', {'folds': selection_summary})
            del model, loss_helper, optimizer, prep, X, V
            gc.collect()
            if device == 'cuda':
                torch.cuda.empty_cache()
        # Regla fijada antes de mirar test; se elige una época >=1, no se exige mejorar base.
        epochs_final = int(np.median(choices))
        logging.info('Épocas finales: mediana(%s)=%d. Ajuste desde base con todo train.', choices, epochs_final)
        prep = clone(make_pipeline().named_steps['preprocesamiento'])
        X = prep.fit_transform(train[FEATURES])
        y, groups = train[TARGET].to_numpy(float), train[GROUP].to_numpy()
        joblib.dump(prep, output/'preprocesador.joblib')
        # TabPFN requiere contexto además de pesos. Sin IDs ni datos de test.
        np.savez_compressed(output/'contexto_train.npz', X=np.asarray(X, dtype=float), y=y)
        model, loss_helper, optimizer = new_training_model(base, args, device, args.seed)
        for epoch in range(1, epochs_final+1):
            loss, steps = train_epoch(model, loss_helper, optimizer, X, y, groups, args, args.seed+10000+epoch)
            native_save(model, output/'ultimo_final.ckpt', epoch)
            write_json(output/'progreso_final.json', {'epoch': epoch, 'epochs_selected': epochs_final,
                                                     'loss': loss, 'optimizer_steps': steps})
        weights = output/'tabpfn_25_finetuned.ckpt'
        native_save(model, weights, epochs_final)
        # Comprobar que se guardaron parámetros distintos de los preentrenados.
        before = torch.load(base, map_location='cpu', weights_only=False)['state_dict']
        after = model.model_.state_dict()
        changed = [key for key in after if key in before and torch.is_tensor(after[key])
                   and not torch.equal(after[key].detach().cpu(), before[key])]
        if not changed:
            raise RuntimeError('No cambió ningún tensor de pesos: no se marca el artefacto como listo.')
        del before, after, model, loss_helper, optimizer
        gc.collect()
        # Roundtrip de checkpoint + preparación + contexto, sobre 3 filas de TRAIN.
        probe = predict_checkpoint(weights, X, y, X[:3], args, device)
        if not np.isfinite(probe).all():
            raise RuntimeError('El checkpoint guardado no produjo predicciones finitas al recargar.')
        test_score = None
        if args.evaluate_test:
            pred = predict_checkpoint(weights, X, y, prep.transform(test[FEATURES]), args, device)
            test_score = metrics(test[TARGET], pred)
            pd.DataFrame({TARGET: test[TARGET], 'prediccion': pred}).to_csv(output/'test_predictions.csv', index=False)
        files = ['tabpfn_25_finetuned.ckpt', 'preprocesador.joblib', 'contexto_train.npz']
        manifest = {**metadata, 'status': 'complete', 'epochs_final': epochs_final,
                    'selection': selection_summary, 'test_metrics': test_score,
                    'changed_weight_tensors': len(changed),
                    'inference': {'n_estimators': args.eval_estimators, 'random_state': args.seed},
                    'files_sha256': {f: sha256(output/f) for f in files},
                    'privacy': 'Paquete local: contiene contexto de entrenamiento transformado con notas; no publicar.',
                    'checkpoint_format': 'save_tabpfn_model de TabPFN 6.4.1; sin contexto embebido en pesos'}
        write_json(output/'manifest.json', manifest)
        write_json(output/'ejecucion.json', {**metadata, 'status': 'complete'})
        print(f'\nCompletado. Paquete para integración: {output}\nPesos: {weights}\n'
              'Conserva también preprocesador.joblib, contexto_train.npz y manifest.json.', flush=True)
        if test_score:
            print(json.dumps(test_score, ensure_ascii=False, indent=2))
    except BaseException as exc:
        write_json(output/'ejecucion.json', {**metadata, 'status': 'interrupted_or_failed',
                                            'error': f'{type(exc).__name__}: {exc}'})
        logging.exception('Ejecución incompleta. Los checkpoints ya guardados permanecen en %s', output)
        raise


def load_bundle(directory, device='cpu'):
    """Cargar después el paquete local para predecir con las 15 columnas originales."""
    prepare_tabpfn_environment()
    from tabpfn import TabPFNRegressor
    directory = Path(directory).resolve()
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'complete':
        raise ValueError('El paquete no está completo.')
    if importlib.metadata.version('tabpfn') != manifest['versions']['tabpfn']:
        raise RuntimeError('Usar la misma versión TabPFN con la que se generó el paquete.')
    for filename, checksum in manifest['files_sha256'].items():
        if sha256(directory/filename) != checksum:
            raise ValueError(f'Checksum incorrecto: {filename}')
    prep = joblib.load(directory/'preprocesador.joblib')
    with np.load(directory/'contexto_train.npz', allow_pickle=False) as context:
        X, y = context['X'], context['y']
    model = TabPFNRegressor(model_path=str(directory/'tabpfn_25_finetuned.ckpt'), device=device,
        **manifest['inference'], n_preprocessing_jobs=1, categorical_features_indices=[],
        fit_mode='low_memory', memory_saving_mode=True, ignore_pretraining_limits=True,
        inference_config={'SUBSAMPLE_SAMPLES': None, 'OUTLIER_REMOVAL_STD': None})
    model.fit(X, y)  # Solo establece contexto; no vuelve a hacer fine-tuning.
    return Pipeline([('preprocesamiento', prep), ('modelo', model)])


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--check-only', action='store_true', help='Verificar preparación y dependencias sin entrenar.')
    p.add_argument('--output-dir', help='Carpeta nueva; por defecto modelos_preentrenados/tabpfn_25/finetuning/fecha.')
    p.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto')
    p.add_argument('--epochs', type=int, default=10, help='Máximo por fold para seleccionar épocas (default: 10).')
    p.add_argument('--patience', type=int, default=3)
    p.add_argument('--learning-rate', type=float, default=1e-5)
    p.add_argument('--weight-decay', type=float, default=.01)
    p.add_argument('--min-delta', type=float, default=1e-4, help='Mejora mínima del RMSE de validación.')
    p.add_argument('--episode-rows', type=int, default=256, help='Tamaño orientativo del episodio de optimización.')
    p.add_argument('--query-ratio', type=float, default=.2)
    p.add_argument('--train-estimators', type=int, default=1)
    p.add_argument('--eval-estimators', type=int, default=4)
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--evaluate-test', action='store_true', help='Evaluar test una vez terminado; nunca para seleccionar.')
    return p


if __name__ == '__main__':
    fine_tune(parser().parse_args())
