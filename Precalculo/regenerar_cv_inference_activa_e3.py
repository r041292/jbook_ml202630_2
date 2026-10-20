"""Regenera la inferencia CV externa vs SVM con el inventario activo de Originales.

Lee folds.csv de la ejecución activa (búsquedas HPO), no entrena ni usa test, y reutiliza
la t corregida y Holm25 de significancia_cv_externa_e3.py. Archiva la inferencia anterior.
Ejecutar: Precalculo/venv/Scripts/python.exe Precalculo/regenerar_cv_inference_activa_e3.py
"""
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from significancia_cv_externa_e3 import FAMILY, REFERENCE, RESULTS, corrected_test

BOOK = Path(__file__).resolve().parent
RUN = RESULTS / 'originales_busquedas' / json.loads(
    (RESULTS / 'originales_busqueda_activa.json').read_text(encoding='utf-8'))['run_id']
DASH = BOOK.parent / 'Dash/data/originales'
ARCHIVE_TAG = 'historico_20261019'


def main():
    folds = pd.read_csv(RUN / 'folds.csv')
    old = pd.read_csv(RUN / 'cv_inference.csv')
    for ext in ('csv', 'json'):  # conservar la inferencia anterior una sola vez
        target = RUN / f'cv_inference_{ARCHIVE_TAG}.{ext}'
        if not target.exists():
            shutil.copyfile(RUN / f'cv_inference.{ext}', target)
    old_report = json.loads((RUN / f'cv_inference_{ARCHIVE_TAG}.json').read_text(encoding='utf-8'))
    ratio = float(old_report['correction_ratio'])
    for name, group in folds.groupby('Modelo'):
        assert len(group) == 5 and set(group.Fold) == set(range(1, 6)) and np.isfinite(group.RMSE).all(), name
    reference = folds.loc[folds.Modelo.eq(REFERENCE)].set_index('Fold').RMSE.sort_index()
    rows = []
    for name, group in folds.groupby('Modelo', sort=True):
        values = group.set_index('Fold').RMSE.sort_index()
        row = dict(Modelo=name, Referencia=REFERENCE, metrica='RMSE medio de folds externos',
                   RMSE_CV=float(values.mean()), SD_RMSE_folds_ddof0=float(values.std(ddof=0)),
                   folds=5, repeticiones=1, ratio_validacion_fit_estudiantes=ratio,
                   familia_ajuste=FAMILY, estado='Evaluado; aproximación exploratoria')
        row.update(corrected_test((values - reference).to_numpy(), ratio))
        if name == REFERENCE:
            row.update(estado='Referencia', familia_ajuste=None)
        rows.append(row)
    table = pd.DataFrame(rows)
    tested = table.Modelo.ne(REFERENCE)
    assert tested.sum() == 25 and not table.loc[tested, 'p_bilateral'].isna().any()
    table['p_Holm'] = np.nan
    table.loc[tested, 'p_Holm'] = multipletests(table.loc[tested, 'p_bilateral'], method='holm')[1]
    table['conclusion'] = ['Referencia' if r.Modelo == REFERENCE else
        ('Mejora significativa' if r.delta_RMSE < 0 else 'Deterioro significativo') if r.p_Holm < .05 else
        'No significativa' for r in table.itertuples()]
    unavailable = {c: None for c in table}
    unavailable.update(Modelo='TabPFN 2.5 fine-tuned', Referencia=REFERENCE, metrica='RMSE medio de folds externos',
                       folds=0, estado='Sin OOF independiente', conclusion='Sin OOF independiente')
    table = pd.concat([table, pd.DataFrame([unavailable])], ignore_index=True).sort_values('RMSE_CV', na_position='last')
    assert list(table.columns) == list(old.columns), 'columnas distintas a la tabla anterior'
    table.to_csv(RUN / 'cv_inference.csv', index=False)
    report = {**old_report, 'regenerado': datetime.now().astimezone().isoformat(),
              'regenerado_motivo': ('Inferencia anterior (19-oct) usaba folds históricos; se recalcula con '
                                    'folds.csv de la ejecución activa, incluida la referencia SVM activa.'),
              'folds_activos_sha256': hashlib.sha256((RUN / 'folds.csv').read_bytes()).hexdigest(),
              'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'archivo_anterior': f'cv_inference_{ARCHIVE_TAG}.csv', 'training_performed': False, 'test_used': False}
    (RUN / 'cv_inference.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for ext in ('csv', 'json'):
        shutil.copyfile(RUN / f'cv_inference.{ext}', DASH / f'cv_inference.{ext}')
    print(table[['Modelo', 'RMSE_CV', 'delta_RMSE', 'p_bilateral', 'p_Holm', 'conclusion']].round(5).to_string(index=False))


if __name__ == '__main__':
    main()
