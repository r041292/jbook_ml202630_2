"""Integridad del paquete público; las fuentes privadas se validan localmente."""
import hashlib
import json

from prepare_data import BOOK, CACHE, ROOT, hashes

PUBLIC_SOURCES = (
    '00_seleccion_base_datos.md',
    'comparacion_aumentacion/comparacion_train.csv',
    'comparacion_aumentacion/seleccion.json',
    'resultados/eda.json',
    'resultados/modelos_lineales.json',
)
ARTIFACTS = (
    'train.csv.gz', 'test.csv.gz', 'fold_metrics.csv', 'coefficients.csv',
    'augmentation.csv.gz', 'comparison_details.json', 'model.joblib', 'manifest.json',
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(manifest):
    packaged = CACHE / 'deployment.json'
    if not packaged.exists():
        if manifest['sha256'] != hashes():
            raise RuntimeError('Las fuentes cambiaron. Regenera los resultados con prepare_data.py y revisa CONTEXT.md.')
        return
    expected = json.loads(packaged.read_text(encoding='utf-8'))
    required = {f'Dash/data/{name}' for name in ARTIFACTS}
    if set(expected['artifacts']) != required:
        raise RuntimeError('El manifiesto de despliegue no contiene todos los artefactos.')
    for relative, digest in expected['artifacts'].items():
        if sha256(ROOT.parent / relative) != digest:
            raise RuntimeError(f'Artefacto de despliegue alterado: {relative}')
    for relative in PUBLIC_SOURCES:
        if sha256(BOOK / relative) != manifest['sha256'][relative]:
            raise RuntimeError(f'Fuente pública alterada: {relative}')
