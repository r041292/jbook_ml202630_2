"""Activa solo una ejecución completa y compatible; no entrena ni predice."""
import json
import sys
from pathlib import Path

import pandas as pd
from entregable3 import OUTPUT, source_hashes, write_json


def activate(run_id):
    if Path(run_id).name != run_id or '/' in run_id or '\\' in run_id:
        raise ValueError('Se necesita únicamente el ID de la ejecución.')
    directory = OUTPUT / 'busquedas' / run_id
    complete = json.loads((directory / 'completo.json').read_text(encoding='utf-8'))
    protocol = json.loads((directory / 'protocolo.json').read_text(encoding='utf-8'))
    selected = json.loads((directory / 'seleccion_antes_test.json').read_text(encoding='utf-8'))
    svm = json.loads((directory / 'modelos_lineales.json').read_text(encoding='utf-8'))
    classic = json.loads((directory / 'clasicos/comparacion.json').read_text(encoding='utf-8'))
    assert complete['status'] == 'completa' and complete['run_id'] == run_id
    assert protocol['source_sha256'] == source_hashes()
    assert selected['test_used_for_selection'] is False
    assert set(selected['models']) == {'svm', 'knn', 'ridge', 'lasso', 'forest', 'xgboost', 'decision_tree'}
    for key, spec in {'svm': svm, **classic['models']}.items():
        optimization = spec['optimization']
        assert len(optimization['methods']) == len(optimization['external_selections']) == 5
        assert spec['best_params'] == selected['models'][key]['params']
        assert spec['selection_rmse'] <= min(r['RMSE'] for r in optimization['methods'])+1e-12
        assert all(r['full_configurations'] > 0 for r in optimization['methods'])
    train = pd.read_csv(directory / 'train.csv.gz')
    test = pd.read_csv(directory / 'test.csv.gz')
    assert len(train) == protocol['partition']['train_valid'] and len(test) == protocol['partition']['test_valid']
    assert not {'estudiante', 'pidm en matricula', 'nota_final', 'fila_fuente'} & set(train)
    write_json(OUTPUT / 'busqueda_activa.json', {'run_id': run_id, 'scope': 'SVM y seis clásicos; Originales conserva sus ejecuciones históricas'})
    print(f'Activada búsqueda completa {run_id}; sincroniza Dash/prepare_data.py.')


if __name__ == '__main__':
    activate(sys.argv[1])
