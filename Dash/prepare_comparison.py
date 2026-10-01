"""Recupera originales de train y reproduce la alternativa 2 solo para comparar.

No vuelve a dividir estudiantes, no utiliza test y no escribe en Precalculo.
El análisis/modelo principal sigue usando exclusivamente perturbación local.
"""
import csv
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def prepare_comparison(book, cache):
    selection = json.loads((book / 'comparacion_aumentacion/seleccion.json').read_text(encoding='utf-8'))
    notebook = json.loads((book / 'precalculo_generar_split_augmented_2.ipynb').read_text(encoding='utf-8'))
    with (book / 'comparacion_aumentacion/Datos_Aleks_Augmented_30000_r_2_train.csv').open(
            encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle, delimiter=';')
        header, selected_rows = next(reader), list(reader)
    count = selection['train_original_filas']
    original_rows = selected_rows[:count]  # La generación conserva los originales al principio.
    namespace = {'display': lambda *args: None}
    previous = Path.cwd()
    try:
        os.chdir(book)
        for index in [2, 4]:
            code = ''.join(notebook['cells'][index]['source'])
            code = code.replace('OUTPUT_DIR.mkdir(exist_ok=True)', '# Sin escritura en la fuente')
            exec(code, namespace)
        # Solo mapeo/precisión; se omite el bloque que divide estudiantes.
        exec(''.join(notebook['cells'][6]['source']).split('groups = defaultdict(list)')[0], namespace)
        for index in [8, 10]:
            exec(''.join(notebook['cells'][index]['source']), namespace)
        exec(''.join(notebook['cells'][12]['source']).split('original_train = to_frame(train_source)')[0], namespace)
        assert header == namespace['output_header']
        seed = selection['semillas_comparacion'][0]
        other_rows, audit = namespace['generate_partition'](original_rows, len(selected_rows), seed, 2)
        original = namespace['to_frame'](original_rows)
        frames = {'Originales de train': original,
                  'Perturbación local': namespace['to_frame'](selected_rows[count:]),
                  'Interpolación entre vecinos': namespace['to_frame'](other_rows[count:])}
        reference = pd.read_csv(book / 'comparacion_aumentacion/comparacion_train.csv',
            sep=';', decimal=',', encoding='utf-8-sig')
        scores = {}
        for alternative, label in [(1, 'Perturbación local'), (2, 'Interpolación entre vecinos')]:
            scores[label] = namespace['distribution_metrics'](original, frames[label])[0]
            expected = reference[(reference['alternativa'] == alternative) & (reference['semilla'] == seed)].iloc[0]
            for metric, value in scores[label].items():
                if not np.isclose(value, expected[metric], atol=1e-12, rtol=1e-10):
                    raise AssertionError(f'No se reproduce {label}: {metric}')
        combined = pd.concat([frame.drop(columns='nota_final').assign(Conjunto=label)
                              for label, frame in frames.items()], ignore_index=True)
        combined.to_csv(cache / 'augmentation.csv.gz', index=False, compression='gzip')
        (cache / 'comparison_details.json').write_text(json.dumps({
            'seed': seed, 'original_rows': count, 'synthetic_rows': len(selected_rows) - count,
            'scores': scores, 'alternative_2_audit': audit,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Comparación gráfica: originales y dos alternativas reproducidos sin tocar las fuentes.', flush=True)
    finally:
        os.chdir(previous)
