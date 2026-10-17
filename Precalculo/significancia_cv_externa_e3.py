"""Comparación exploratoria de RMSE externo con t corregida y Holm, sin entrenar."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from statsmodels.stats.multitest import multipletests

BOOK = Path(__file__).resolve().parent
RESULTS = BOOK / 'resultados/e3'
OUTPUT = RESULTS / 'cv_externa'
REFERENCE = 'SVM lineal'
FAMILY = 'Holm24 CV vs SVM'
FOLD_FOLDERS = ['clasicos', 'scopus/xbart', 'scopus/catboost', 'scopus/copilot', 'scopus/kernel_ridge',
                'logicdt', 'tabpfn_25', 'rim', 'tabicl_v2', 'hrt_boost', 'tcr_xgboost', 'tabfm',
                'gpr_xgb', 'svr_rbf_raffle/svr_rbf', 'svr_rbf_raffle/raffle',
                'xgboost_variantes/gbtree', 'xgboost_variantes/dart', 'xgboost_variantes/denseweight', 'linxgboost']


def input_paths():
    return [RESULTS / f'{folder}/fold_metrics.csv' for folder in FOLD_FOLDERS] + [
        RESULTS / 'modelos_lineales.json',
        RESULTS / 'resumen_completo/modelos.csv']


def corrected_test(differences, ratio):
    """Adaptación exploratoria a 1×5 GroupKFold; s² con ddof=1 y df=4."""
    values = np.asarray(differences, dtype=float)
    if values.shape != (5,) or not np.isfinite(values).all() or not np.isfinite(ratio) or ratio <= 0:
        raise ValueError('Se requieren cinco diferencias pareadas finitas y ratio positivo.')
    mean = float(values.mean())
    variance = float(values.var(ddof=1))
    se = float(np.sqrt((1/len(values) + ratio)*variance))
    if se == 0:
        # Sin estimación de variabilidad no declarar evidencia infinita artificial.
        return dict(delta_RMSE=mean, SE_corregido=se, t_corregida=None, df=4,
                    p_bilateral=None, IC95_delta_inferior=None, IC95_delta_superior=None)
    statistic = mean/se
    half_width = float(student_t.ppf(.975, df=4)*se)
    return dict(delta_RMSE=mean, SE_corregido=se, t_corregida=statistic, df=4,
                p_bilateral=float(2*student_t.sf(abs(statistic), df=4)),
                IC95_delta_inferior=mean-half_width, IC95_delta_superior=mean+half_width)


def build():
    sources = input_paths()
    frames = [pd.read_csv(RESULTS / f'{folder}/fold_metrics.csv') for folder in FOLD_FOLDERS]
    folds = pd.concat(frames, ignore_index=True)[['Modelo', 'Fold', 'RMSE', 'MAE', 'MAPE (%)', 'R²']]
    folds['Modelo'] = folds.Modelo.replace({'TabPFN 2.5 (4 estimadores, CPU)': 'TabPFN 2.5 original'})
    inventory = pd.read_csv(RESULTS / 'resumen_completo/modelos.csv')
    expected = set(inventory.Modelo) - {'TabPFN 2.5 fine-tuned'}
    if set(folds.Modelo) != expected or folds.duplicated(['Modelo', 'Fold']).any():
        raise ValueError('Inventario o pares modelo-fold incompatibles.')
    for name, group in folds.groupby('Modelo'):
        if len(group) != 5 or set(group.Fold) != set(range(1, 6)) or not np.isfinite(group.RMSE).all():
            raise ValueError('Folds incompletos: ' + name)
    baseline = json.loads((RESULTS / 'modelos_lineales.json').read_text(encoding='utf-8'))
    audit = baseline['fold_audit']
    if len(audit) != 5 or any(row['shared_students'] != 0 for row in audit):
        raise ValueError('Auditoría de folds inválida.')
    # La unidad de partición es el estudiante; se documenta esta adaptación.
    ratios = [row['validation_students']/row['fit_students'] for row in audit]
    ratio = float(np.mean(ratios))
    reference = folds.loc[folds.Modelo.eq(REFERENCE)].set_index('Fold').RMSE.sort_index()
    rows = []
    for name, group in folds.groupby('Modelo', sort=True):
        values = group.set_index('Fold').RMSE.sort_index()
        row = dict(Modelo=name, Referencia=REFERENCE, metrica='RMSE medio de folds externos',
                   RMSE_CV=float(values.mean()), SD_RMSE_folds_ddof0=float(values.std(ddof=0)),
                   folds=5, repeticiones=1, ratio_validacion_fit_estudiantes=ratio,
                   familia_ajuste=FAMILY, estado='Evaluado; aproximación exploratoria')
        row.update(corrected_test((values-reference).to_numpy(), ratio))
        if name == REFERENCE:
            row.update(estado='Referencia', familia_ajuste=None)
        rows.append(row)
    table = pd.DataFrame(rows)
    tested = table.Modelo.ne(REFERENCE)
    if tested.sum() != 24 or table.loc[tested, 'p_bilateral'].isna().any():
        raise ValueError('Se esperaban 24 contrastes válidos vs SVM.')
    table['p_Holm'] = np.nan
    table.loc[tested, 'p_Holm'] = multipletests(table.loc[tested, 'p_bilateral'], method='holm')[1]
    table['conclusion'] = ['Referencia' if row.Modelo == REFERENCE else
        ('Mejora significativa' if row.delta_RMSE < 0 else 'Deterioro significativo') if row.p_Holm < .05 else
        'No significativa' for row in table.itertuples()]
    unavailable = {column: None for column in table}
    unavailable.update(Modelo='TabPFN 2.5 fine-tuned', Referencia=REFERENCE, metrica='RMSE medio de folds externos',
                       folds=0, estado='Sin OOF independiente', conclusion='Sin OOF independiente')
    table = pd.concat([table, pd.DataFrame([unavailable])], ignore_index=True).sort_values('RMSE_CV', na_position='last')
    OUTPUT.mkdir(exist_ok=True)
    table.to_csv(OUTPUT / 'contrastes_vs_svm.csv', index=False)
    folds.sort_values(['Modelo', 'Fold']).to_csv(OUTPUT / 'fold_metrics.csv', index=False)
    report = dict(reference=REFERENCE, primary_metric='media aritmética RMSE de 5 folds externos',
                  method='t pareada corregida Nadeau–Bengio; adaptación exploratoria a 1×5 GroupKFold',
                  formula='SE=sqrt((1/5+mean(n_val_estudiantes/n_fit_estudiantes))*var(delta_RMSE,ddof=1)); t=mean(delta)/SE; df=4; p=2*sf(abs(t))',
                  fold_audit=audit, correction_ratio=ratio, family_size=24, family=FAMILY,
                  training_performed=False, test_used=False,
                  excluded_candidates={'GPR sola (ablación)': 'Retirada por solicitud del usuario por trazabilidad del artefacto original; se conserva el antecedente archivado.'},
                  family_redefined_after_review=True,
                  limitations=['Una sola partición de cinco folds, sin repeticiones: aproximación de baja potencia.',
                               'La corrección aproxima la dependencia por solapamiento; no garantiza inferencia exacta para GroupKFold.',
                               'Comparación exploratoria: búsqueda histórica de familias y grillas sobre el mismo train; familia no anidada.',
                               'IC marginales sin corrección múltiple; Holm se aplica solo a los 24 p de RMSE vs SVM.',
                               'No es un contraste entre todos los pares ni demuestra equivalencia cuando p>=0.05.'],
                  sources_sha256={p.relative_to(BOOK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  references=['https://doi.org/10.1023/A:1024068626366',
                              'https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_stats.html',
                              'https://www.jmlr.org/papers/v5/grandvalet04a.html'])
    (OUTPUT / 'reporte.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# CV externa: comparación exploratoria frente al SVM', '',
             'La comparación principal de procedimientos usa CV externa; el test temporal contrasta el periodo posterior.',
             'Los rankings distintos responden a muestras y objetivos de generalización diferentes. No elegir familia por test.', '',
             '## Método y alcance', '',
             'Se reutilizan los cinco folds externos canónicos, sin entrenar ni usar métricas o predicciones de test en el cálculo. Se empareja el RMSE de cada modelo con SVM en el mismo fold.',
             'Adaptación aproximada del test t corregido de Nadeau–Bengio: `SE²=(1/5+q)*s²`, `t=media(delta)/SE`, 4 grados de libertad, p bilateral.',
             f'`s²` usa ddof=1; `q` es la media de estudiantes_validación/estudiantes_fit ({ratio:.9f}). El RMSE sigue ponderando registros dentro de cada fold.',
             'Holm corrige conjuntamente los **24 contrastes RMSE vs SVM** del inventario activo. SVM y TabPFN fine-tuned no entran en la familia. GPR sola fue retirada por trazabilidad del artefacto original; el híbrido GPR–XGBoost sigue siendo un experimento distinto.',
             'Se conserva la misma familia en el tablero clásico; no se recalcula Holm sobre sus cinco modelos.', '',
             'Hay una sola partición 1×5, no CV repetida: la corrección es una aproximación exploratoria, con poca potencia. Los folds no son observaciones independientes.',
             'No se usa t ordinaria ni permutación IID de filas OOF. No se garantiza calibración exacta de p para GroupKFold. Los IC95% son marginales.',
             'La familia y las grillas se han explorado sobre el mismo train; esto no evalúa de forma independiente un selector de familia anidado.', '',
             '## Resultados', '', '| Modelo | RMSE medio CV | Δ vs SVM | p bilateral corregida | p Holm24 | Conclusión |',
             '|---|---:|---:|---:|---:|---|']
    for row in table.itertuples():
        fmt = lambda value: '—' if pd.isna(value) else f'{value:.6f}'
        lines.append(f'| {row.Modelo} | {fmt(row.RMSE_CV)} | {fmt(row.delta_RMSE)} | {fmt(row.p_bilateral)} | {fmt(row.p_Holm)} | {row.conclusion} |')
    best = table.iloc[0]
    improved = table.conclusion.eq('Mejora significativa').sum()
    lines += ['', '## Conclusión', '',
              f'{best.Modelo} lidera numéricamente CV: RMSE medio {best.RMSE_CV:.6f}; p bilateral {best.p_bilateral:.6f}, Holm24 {best.p_Holm:.6f} frente al SVM.',
              f'{improved} mejoras frente al SVM sobreviven Holm24. Ausencia de significancia no prueba igualdad.',
              'El mínimo de CV es un candidato para validación futura, no un ganador confirmado. SVR RBF conserva el mínimo descriptivo del test, sin reemplazar el criterio CV.', '',
              '## Referencias', '', *[f'- {url}' for url in report['references']], '',
              'Reproducir: `venv/Scripts/python.exe significancia_cv_externa_e3.py`. No reentrena ni cambia predicciones.']
    (OUTPUT / 'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(table[['Modelo', 'RMSE_CV', 'p_bilateral', 'p_Holm', 'conclusion']].to_string(index=False))
    return table


if __name__ == '__main__':
    build()
