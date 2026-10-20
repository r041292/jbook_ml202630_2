"""Contrastes pareados complementarios de TR-KRR en el test temporal E3."""
import hashlib
import json

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from entregable3 import BOOK, OUTPUT, TARGET, GROUP, write_json
from evaluar_tabpfn25_finetuned_e3 import paired_comparison
from evaluacion_nuevos_e3 import partitions


MODEL = 'Truncated Newton KRR RBF'
REFERENCES = ('SVM lineal', 'XGBoost')
FAMILY = 'Holm2 TR-KRR vs SVM/XGBoost'
FOLDER = OUTPUT / 'tn_krr'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    _, test, _, _ = partitions()
    model = pd.read_csv(FOLDER / 'test_predictions.csv.gz')
    svm = pd.read_csv(OUTPUT / 'test.csv.gz')
    classic = pd.read_csv(OUTPUT / 'clasicos/test_predictions.csv.gz')
    for candidate, label in [(model, MODEL), (svm, 'SVM lineal'), (classic, 'XGBoost')]:
        if len(candidate) != len(test):
            raise ValueError(f'Tamaño incompatible en predicciones {label}.')
        if 'fila_fuente' in candidate:
            np.testing.assert_array_equal(candidate.fila_fuente, test.fila_fuente)
    for candidate in [model, svm, classic]:
        if TARGET in candidate:
            np.testing.assert_allclose(candidate[TARGET], test[TARGET], atol=1e-12, rtol=0)

    reference_predictions = {
        'SVM lineal': svm['svm'].to_numpy(float),
        'XGBoost': classic['xgboost'].to_numpy(float),
    }
    rows = []
    for reference in REFERENCES:
        contrast = paired_comparison(test[TARGET].to_numpy(float),
                                     model['prediccion'].to_numpy(float),
                                     reference_predictions[reference],
                                     test[GROUP].to_numpy())
        for row in contrast:
            rows.append({'Modelo': MODEL, 'Referencia': reference, **row})

    for row in rows:
        row['diferencia_candidato_menos_referencia'] = row.pop(
            'diferencia_ajustado_menos_referencia')

    raw = [next(row['p_bilateral'] for row in rows
                if row['Referencia'] == reference and row['metrica'] == 'RMSE')
           for reference in REFERENCES]
    adjusted = multipletests(raw, method='holm')[1]
    for row in rows:
        index = REFERENCES.index(row['Referencia'])
        row['familia_ajuste'] = FAMILY
        row['p_ajustado'] = float(adjusted[index])
        row['significativa_al_5%'] = bool(adjusted[index] < 0.05)
        row['fuente'] = 'resultados/e3/tn_krr/contrastes_test.csv'

    table = pd.DataFrame(rows)
    table.to_csv(FOLDER / 'contrastes_test.csv', index=False)
    sources = ['significancia_tn_krr_e3.py', 'evaluar_tabpfn25_finetuned_e3.py',
               'evaluacion_nuevos_e3.py', 'resultados/e3/tn_krr/test_predictions.csv.gz',
               'resultados/e3/test.csv.gz', 'resultados/e3/clasicos/test_predictions.csv.gz']
    report = {
        'model': MODEL,
        'references': list(REFERENCES),
        'family': FAMILY,
        'family_size': len(REFERENCES),
        'method': 'Permutation test paired by student (99,999 resamples); bootstrap by student (10,000 resamples); seed 42.',
        'note': 'RMSE and R² share the SSE permutation p-value. Holm2 covers only the two predeclared references for this supplemental TR-KRR analysis; it is not the historical global Holm55 family.',
        'test_used_for_selection': False,
        'partition': 202530,
        'rows': table.to_dict('records'),
        'sources_sha256': {path: sha256(BOOK / path) for path in sources},
    }
    write_json(FOLDER / 'contrastes_test.json', report)
    print(table[['Modelo', 'Referencia', 'metrica',
                 'diferencia_candidato_menos_referencia', 'p_bilateral',
                 'p_ajustado', 'familia_ajuste']].to_string(index=False))
    return table


if __name__ == '__main__':
    build()
