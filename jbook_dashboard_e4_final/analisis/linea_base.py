"""Registra (o verifica) el estado del libro previo `jbook_dashboard/`.

Uso: python linea_base.py [--verificar]. Excluye `_build/`, que es salida regenerable.
No modifica ningún archivo del libro previo.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / 'jbook_dashboard'
OUT = HERE / 'salidas' / 'linea_base_jbook_dashboard.json'


def inventario():
    rows = {}
    for path in sorted(OLD.rglob('*')):
        rel = path.relative_to(OLD).as_posix()
        if path.is_file() and not rel.startswith('_build/'):
            rows[rel] = {'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return rows


if __name__ == '__main__':
    actual = inventario()
    if '--verificar' in sys.argv:
        base = json.loads(OUT.read_text(encoding='utf-8'))['archivos']
        cambios = sorted(set(base) ^ set(actual) | {k for k in base.keys() & actual.keys() if base[k] != actual[k]})
        print('Sin cambios' if not cambios else f'Cambios: {cambios}')
        sys.exit(1 if cambios else 0)
    OUT.write_text(json.dumps({'carpeta': 'jbook_dashboard', 'excluye': ['_build/'],
                               'n_archivos': len(actual), 'archivos': actual},
                              ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(actual)} archivos registrados en {OUT.name}')
