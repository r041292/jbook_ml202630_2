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
    assert original.BEST_NAME == 'Kernel Ridge RBF'
    assert original.CATALOG[original.TN_KRR]['name'] == 'Truncated Newton KRR RBF'
    assert 'gpr_solo' not in original.CATALOG
    training, test = original.combined_frames(app.TRAIN, app.TEST)
    assert (len(training), len(test)) == (1309, 188)
    assert not {'nota_final', 'fila_fuente', 'estudiante', 'pidm en matricula'} & set(training)
    cv = original.comparison_rows(training, app.TARGET, cv=True)
    inference = add_inference(cv, cv=True)
    assert inference[P_HOLM].notna().sum() == 25
    assert cv.iloc[0].Modelo == original.BEST_NAME
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
                output = prefix+'-comparison.children'
                metadata = app.app.callback_map[output]
                inputs = [{**item, 'value': value} for item, value in zip(metadata['inputs'], [program, course, partition])]
                response = client.post('/_dash-update-component', json={
                    'output': output, 'outputs': {'id': prefix+'-comparison', 'property': 'children'},
                    'inputs': inputs, 'state': [], 'changedPropIds': [inputs[0]['id']+'.value']})
                assert response.status_code == 200, response.get_data(as_text=True)[:1000]
    predict = app.app.callback_map['original-prediction-result.children']['callback'].__wrapped__
    result = str(predict(1, original.BEST, *[app.DEFAULTS[c] for c in app.NUMERIC+app.CATEGORICAL]))
    assert 'Nota predicha' in result and 'Kernel Ridge RBF' in result
    tn_result = str(predict(1, original.TN_KRR, *[app.DEFAULTS[c] for c in app.NUMERIC+app.CATEGORICAL]))
    assert 'Truncated Newton KRR RBF' in tn_result
    from classic_models import load_model
    from lime_xgboost import explain_xgboost
    explanation = explain_xgboost(load_model('xgboost'), app.TRAIN, app.TEST.iloc[[0]], app.LABELS, 1000)
    assert explanation['neighborhood'] == 'empirical' and explanation['incoherent_fraction'] == 0
    assert np.isfinite(explanation['fidelity'])
    np.testing.assert_allclose(explanation['prediction'], float(load_model('xgboost').predict(app.TEST[app.FEATURES].iloc[[0]])[0]), atol=1e-10)
    print(json.dumps({'status': 'ok', 'models': 27, 'cv_contrasts': 24,
                      'leader': original.BEST_NAME, 'canonical_test_predictions_verified': 188,
                      'http_and_filtered_callbacks': 'ok', 'model_refit': False}))


if __name__ == '__main__':
    validate()
