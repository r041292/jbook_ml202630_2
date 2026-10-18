"""Medidas de pared auditables; sin datos de personas ni valores de entrada."""
import hashlib
import json
import os
import platform
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sklearn
from threadpoolctl import threadpool_info

ZONE = timezone(timedelta(hours=-5), 'America/Bogota')
ROOT = Path(__file__).resolve().parent.parent


class TimingRun:
    def __init__(self, label, metadata=None):
        self.run_id = datetime.now(ZONE).strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:8]
        self.directory = ROOT / 'tiempos' / self.run_id
        self.directory.mkdir(parents=True)
        self.path = self.directory / 'eventos.jsonl'
        self.label = label
        self.started = datetime.now(ZONE).isoformat()
        self.clock = time.perf_counter()
        self.rows = []
        self.metadata = {'label': label, 'run_id': self.run_id, 'started': self.started,
                         'platform': platform.platform(), 'cpu': platform.processor(),
                         'logical_cpus': os.cpu_count(), 'device': 'CPU; GPU no utilizada',
                         'python': sys.version, 'sklearn': sklearn.__version__,
                         'threadpools': threadpool_info(), 'ram': 'No medida', **(metadata or {})}
        (self.directory / 'metadata.json').write_text(json.dumps(self.metadata, indent=2, ensure_ascii=False), encoding='utf-8')

    def record(self, stage, batch, seconds, rows=None, status='completa', **details):
        event = {'stage': stage, 'batch': batch, 'seconds': seconds, 'rows': rows,
                 'status': status, 'recorded': datetime.now(ZONE).isoformat(), **details}
        self.rows.append(event)
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, ensure_ascii=False, default=str) + '\n')

    @contextmanager
    def measure(self, stage, batch, rows=None, **details):
        started = datetime.now(ZONE).isoformat()
        clock = time.perf_counter()
        status = 'completa'
        try:
            yield
        except BaseException as error:
            status = 'fallida'
            details['error'] = type(error).__name__ + ': ' + str(error)
            raise
        finally:
            self.record(stage, batch, time.perf_counter()-clock, rows, status,
                        started=started, **details)

    def finish(self, status='completa'):
        self.record('Total del experimento', self.label, time.perf_counter()-self.clock, status=status,
                    scope='Medida directa; incluye E/S y validaciones; no sumar con las etapas')
        relative = self.directory.relative_to(ROOT).as_posix()
        body = f'\n### Ejecución `{self.run_id}`\n\n'
        body += f'- **Modelo/motivo:** {self.label}.\n- **Fecha/zona:** {self.started} a {datetime.now(ZONE).isoformat()}; America/Bogota.\n'
        body += f'- **Estado:** {status}. **Entorno/configuración/código/datos:** [{relative}/metadata.json]({relative}/metadata.json).\n'
        body += '- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.\n'
        body += f'- **Evidencia cruda:** [eventos]({relative}/eventos.jsonl).\n\n'
        body += '| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |\n| --- | --- | ---: | ---: | --- | --- | --- |\n'
        for index, row in enumerate(self.rows, 1):
            body += f'| {row["stage"]} | {row["batch"]} | {row["seconds"]:.9f} | {row["rows"] if row["rows"] is not None else "No aplica"} | 1 | {row["status"]} | Total; eventos.jsonl línea {index} |\n'
        with (ROOT / 'TIEMPOS_EJECUCION.md').open('a', encoding='utf-8') as stream:
            stream.write(body)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def predict_application(model, frame):
    """Cada consulta del simulador conserva su lote y hash del modelo ajustado."""
    import joblib
    run = TimingRun(type(model.steps[-1][1]).__name__ + ' · inferencia de aplicación',
                    {'script': 'Dash/prediction.py', 'script_sha256': file_hash(Path(__file__).with_name('prediction.py')),
                     'model_hash': joblib.hash(model), 'batch_size': len(frame),
                     'n_jobs': getattr(model.steps[-1][1], 'n_jobs', None),
                     'features': list(frame.columns), 'data': 'Formulario; valores personales no registrados'})
    status = 'completa'
    try:
        with run.measure('Inferencia', 'aplicación', len(frame)):
            return model.predict(frame)
    except BaseException:
        status = 'fallida'
        raise
    finally:
        run.finish(status)
