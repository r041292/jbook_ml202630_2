"""Copia las fuentes reutilizadas al libro E4 y escribe `source_manifest.json`.

El libro nunca lee archivos de `../jbook_dashboard/`, `../Precalculo/` ni `../Dash/` en el
build: este script copia aquí el código que se muestra con `literalinclude` y las tablas
estadísticas heredadas, y registra el SHA-256 del origen y de la copia. Después lista con su
hash cada capítulo, imagen y salida del libro. Ejecutar al cerrar cada fase.
"""
import hashlib
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
ROOT = BOOK.parent

COPIES = {
    'analisis/codigo/tn_krr_e3.py': 'Precalculo/tn_krr_e3.py',
    'analisis/codigo/gpr_xgb_hpo_e3.py': 'Precalculo/gpr_xgb_hpo_e3.py',
    'analisis/codigo/evaluar_gpr_xgb_e3.py': 'Precalculo/evaluar_gpr_xgb_e3.py',
    'analisis/codigo/modelos_scopus_e3.py': 'Precalculo/modelos_scopus_e3.py',
    'analisis/codigo/entregable3.py': 'Precalculo/entregable3.py',
    'analisis/codigo/modelos_clasicos.py': 'Precalculo/modelos_clasicos.py',
    'analisis/codigo/busquedas_hiperparametros_e3.py': 'Precalculo/busquedas_hiperparametros_e3.py',
    'analisis/codigo/student_dm.py': 'Dash/student_dm.py',
    'analisis/codigo/classic_posthoc.py': 'Dash/classic_posthoc.py',
    'analisis/codigo/render.yaml': 'render.yaml',
    'analisis/codigo/dashboard-ci.yml': 'RenderDeploy/.github/workflows/dashboard-ci.yml',
}
for family in ('clasicos', 'originales'):
    folder = ROOT / 'jbook_dashboard' / f'analisis_{family}' / 'salidas'
    for path in sorted(folder.glob('*.csv')) + sorted(folder.glob('*.json')):
        if path.name.startswith(('stats_', 'eval_', 'hpo_resumen', 'hpo_metodo', 'tiempos_', 'shap_')):
            COPIES[f'analisis/salidas/heredadas/{family}/{path.name}'] = path.relative_to(ROOT).as_posix()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    copies = {}
    for target, source in COPIES.items():
        src, dst = ROOT / source, BOOK / target
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        copies[target] = {'origen': source, 'sha256_origen': sha(src), 'sha256_copia': sha(dst)}
    files = {}
    for path in sorted(BOOK.rglob('*')):
        rel = path.relative_to(BOOK).as_posix()
        if path.is_file() and not rel.startswith(('_build/', '_interno/', 'analisis/__pycache__')) and rel not in ('source_manifest.json', 'CONTEXT.md'):
            files[rel] = sha(path)
    manifest = {'generado': datetime.now(timezone(timedelta(hours=-5))).isoformat(timespec='seconds'),
                'ejecuciones_fuente': {'busqueda_activa_base': '20261018_102325_af643f83',
                                       'originales_activa': '20261020_153034_consolidada'},
                'copias': copies, 'archivos': files}
    (BOOK / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(copies)} copias y {len(files)} archivos registrados.')


if __name__ == '__main__':
    main()
