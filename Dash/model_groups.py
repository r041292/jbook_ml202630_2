"""Modelos de Originales que son una librería importada o un modelo preentrenado.

Decisión del usuario (20-oct-2026): el proyecto se concentra en los modelos clásicos y las implementaciones
propias. Estos 11 modelos se conservan como referencia, pero se ocultan por defecto (botón al inicio de la
pestaña) y se excluyen de todas las pruebas estadísticas de «Conclusiones y comparación estadística · Originales».
Las claves son las del catálogo (EXPERIMENTS en prepare_originals.py); los nombres se validan para evitar deriva.
"""
IMPORT_ONLY = {
    'm1': 'TabICLv2',
    'm2': 'TabPFN 2.5 original',
    'm4': 'TabPFN 2.5 fine-tuned',
    'm6': 'CatBoost',
    'm8': 'TabFM 1.0.0 (PyTorch CPU, 32 vistas)',
    'm9': 'XGBoost ampliado (gbtree)',
    'm10': 'RaFFLE',
    'm12': 'DART-XGBoost',
    'm13': 'HRT-Boost',
    'm17': 'XBART (GFR)',
    'm18': 'coPILOT',
}
REASON = ('Librería importada sin implementación propia' )


def validate(catalog):
    """Falla si una clave ya no corresponde al modelo esperado."""
    for key, name in IMPORT_ONLY.items():
        if catalog[key]['name'] != name:
            raise ValueError(f'La clave {key} ya no es {name!r}: {catalog[key]["name"]!r}')


def is_import_only(key):
    return key in IMPORT_ONLY
