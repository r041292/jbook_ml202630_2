"""Integridad del paquete público; las fuentes privadas se validan localmente."""
import hashlib
import json

from prepare_data import BOOK, CACHE, ROOT, hashes, CLASSIC_FILES

PUBLIC_SOURCES = (
    '00_seleccion_base_datos.md',
    'resultados/e3/eda.json',
    'resultados/e3/modelos_lineales.json',
    'resultados/e3/particion.json',
    'resultados/e3/grid_search.csv',
    'resultados/e3/clasicos/comparacion.json',
)
ARTIFACTS = (
    'train.csv.gz', 'test.csv.gz', 'fold_metrics.csv', 'coefficients.csv',
    'grid_search.csv', 'model.joblib', 'manifest.json',
) + tuple('clasicos/' + name for name in CLASSIC_FILES)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(manifest):
    for relative, digest in manifest['artifact_sha256'].items():
        if sha256(CACHE / relative) != digest:
            raise RuntimeError('Artefacto alterado: ' + relative)
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
