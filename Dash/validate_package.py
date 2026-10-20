"""Valida el paquete publicable sin fuentes privadas ni reentrenamiento."""
import json

import numpy as np

import app
import original_models as original
from deployment import verify_inputs
from statistical_comparison import add_inference, P_HOLM


def validate():
    verify_inputs(app.MANIFEST)
    assert len(original.CATALOG) == 27
    assert original.BEST_NAME == original.ACTIVE['best_name']
    assert original.CATALOG[original.TN_KRR]['name'] == 'Truncated Newton KRR RBF'
    assert 'gpr_solo' not in original.CATALOG
    training, test = original.combined_frames(app.TRAIN, app.TEST)
    assert (len(training), len(test)) == (1309, 188)
    assert not {'nota_final', 'fila_fuente', 'estudiante', 'pidm en matricula'} & set(training)
    cv = original.comparison_rows(training, app.TARGET, cv=True)
    from statistical_comparison import CV_INFERENCE
    assert CV_INFERENCE.p_Holm.notna().sum()==25  # Archivo histórico; no aplicar a métricas nuevas.
    assert original.ANALYSIS['students']['family_size']==14  # 11 modelos de librería importada fuera de las pruebas
    assert original.ANALYSIS['omnibus']['n_models']==15
    assert cv.iloc[0].Modelo == original.BEST_NAME
    from model_groups import IMPORT_ONLY, validate as validate_groups
    validate_groups(original.CATALOG)
    assert not set(IMPORT_ONLY.values()) & set(cv.Modelo), 'Los modelos de librería importada deben estar ocultos por defecto.'
    assert set(IMPORT_ONLY.values()) <= set(original.comparison_rows(training, app.TARGET, cv=True, show_imports=True).Modelo)
    assert set(original.ANALYSIS['excluded_library']) == set(IMPORT_ONLY.values())
    np.testing.assert_allclose(original.best_model().predict(test[app.FEATURES]), test[original.BEST], atol=1e-12, rtol=0)
    np.testing.assert_allclose(original.model_for(original.TN_KRR).predict(test[app.FEATURES]),
                               test[original.TN_KRR], atol=1e-10, rtol=0)
    client = app.server.test_client()
    for route in ['/', '/healthz', '/_dash-layout', '/_dash-dependencies', '/assets/style.css']:
        assert client.get(route).status_code == 200, route
    layout = client.get('/_dash-layout').get_json()
    ids = []
    def visit(value):
        if isinstance(value, dict):
            if 'props' in value and 'id' in value['props']:
                ids.append(value['props']['id'])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(layout)
    assert len(ids) == len(set(ids))
    for prefix in ['original', 'classic']:
        for program, course in [('__all__', '__all__'), ('Ingeniería Civil', 'MAT1101'), ('Arquitectura', 'MAT1101')]:
            for partition in ['cv', 'test']:
                # Originales tiene además el estado del botón de modelos de librería importada (oculto/visible).
                for extra in ([[False], [True]] if prefix == 'original' else [[]]):
                    output = prefix+'-comparison.children'
                    metadata = app.app.callback_map[output]
                    inputs = [{**item, 'value': value} for item, value in zip(metadata['inputs'], [program, course, partition, *extra])]
                    response = client.post('/_dash-update-component', json={
                        'output': output, 'outputs': {'id': prefix+'-comparison', 'property': 'children'},
                        'inputs': inputs, 'state': [], 'changedPropIds': [inputs[0]['id']+'.value']})
                    assert response.status_code == 200, response.get_data(as_text=True)[:1000]
    assert 'original-prediction-result.children' not in app.app.callback_map
    from classic_models import load_model
    import classic_models as classics
    tree = load_model('decision_tree')
    np.testing.assert_allclose(tree.predict(app.TEST[app.FEATURES]),
                               classics.TEST_PREDICTIONS.decision_tree, atol=1e-12, rtol=0)
    assert (classics.FRIEDMAN['n_models'], classics.FRIEDMAN['n_folds']) == (7, 5)
    assert 'decision_tree' in classics.NAMES and 'dummy' not in classics.ALL_NAMES
    from student_comparison import load as load_student_comparison, section as student_section, holm
    student = load_student_comparison(app.CACHE)
    assert (student['n_students'], student['n_records'], student['family_size']) == (188, 188, 6)
    assert student['active_run'] == classics.REPORT.get('run_id') and student['reps'] == 49999
    np.testing.assert_allclose([r['p_holm'] for r in student['rows']], holm([r['p_raw'] for r in student['rows']]))
    tables = []
    from dash import html
    student_layout = student_section(student, {'md': lambda value: html.Div(value),
        'table': lambda frame: tables.append(frame) or html.Div()})
    assert len(tables[0]) == 5 and 'p Holm' not in ' '.join(tables[0].columns)
    assert 'Etapa 3' in str(student_layout)
    comparison = app.app.callback_map['classic-comparison.children']['callback'].__wrapped__('__all__', '__all__', 'cv')
    text = str(comparison)
    assert text.index('Etapa 3 · Diebold–Mariano por estudiante') < text.index('Tamaño del efecto · pérdidas MSE por fold')
    shap = app.app.callback_map['classic-shap-result.children']['callback'].__wrapped__('__all__', '__all__', 'all')
    assert 'Caso 0124' in str(shap) and 'Caso 0118' in str(shap)
    if app.MODEL_REPORT.get('optimization'):
        np.testing.assert_allclose(app.MODEL.predict(app.TEST[app.FEATURES]), app.TEST.svm, atol=1e-12, rtol=0)
        for key in classics.NAMES:
            np.testing.assert_allclose(load_model(key).predict(app.TEST[app.FEATURES]),
                                       classics.TEST_PREDICTIONS[key], atol=1e-12, rtol=0)
        for spec in [app.MODEL_REPORT, *classics.REPORT['models'].values()]:
            optimization = spec['optimization']
            assert len(optimization['methods']) == len(optimization['external_selections']) == 5
            assert len(optimization['evolution']) == 4
            assert abs(spec['selection_rmse']-min(m['RMSE'] for m in optimization['methods'])) < 1e-12
            assert sum(r['stage'] == 'Búsqueda' for r in optimization['timings']) == 30
    from lime_xgboost import explain_xgboost
    explanation = explain_xgboost(load_model('xgboost'), app.TRAIN, app.TEST.iloc[[0]], app.LABELS, 1000)
    assert explanation['neighborhood'] == 'empirical' and explanation['incoherent_fraction'] == 0
    assert np.isfinite(explanation['fidelity'])
    np.testing.assert_allclose(explanation['prediction'], float(load_model('xgboost').predict(app.TEST[app.FEATURES].iloc[[0]])[0]), atol=1e-10)
    print(json.dumps({'status': 'ok', 'models': 27, 'classic_models': 7, 'cv_contrasts': 25,
                      'leader': original.BEST_NAME, 'canonical_test_predictions_verified': 188,
                      'http_and_filtered_callbacks': 'ok', 'model_refit': False,
                      'student_contrasts_holm': 6, 'student_table_sorted': True,
                      'shap_global_and_two_local_cases': 'ok'}))


if __name__ == '__main__':
    validate()
