"""Descarga exclusivamente el checkpoint de regresión oficial TabPFN 2.5."""
import hashlib
import json
import urllib.request

from evaluacion_nuevos_e3 import MODEL_DIR, CHECKPOINT
from entregable3 import write_json


def download():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    # API pública: fijar un commit exacto en lugar de depender de main al ejecutar.
    url = 'https://huggingface.co/api/models/Prior-Labs/tabpfn_2_5'
    with urllib.request.urlopen(url) as response:
        revision = json.load(response)['sha']
    url = f'https://huggingface.co/Prior-Labs/tabpfn_2_5/resolve/{revision}/{CHECKPOINT}'
    target = MODEL_DIR / CHECKPOINT
    temp = target.with_suffix('.download')
    urllib.request.urlretrieve(url, temp)
    if temp.stat().st_size < 1_000_000:
        raise ValueError('La respuesta no es un checkpoint válido')
    checksum = hashlib.sha256(temp.read_bytes()).hexdigest()
    temp.replace(target)
    manifest = {'repository': 'Prior-Labs/tabpfn_2_5', 'revision': revision,
                'filename': CHECKPOINT, 'url': url, 'sha256': checksum,
                'bytes': target.stat().st_size,
                'license_url': 'https://huggingface.co/Prior-Labs/tabpfn_2_5/blob/main/LICENSE'}
    write_json(MODEL_DIR / 'procedencia.json', manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    download()
