"""Cerrar artefactos de la ejecución activa cuando termina CatBoost."""
import json
import subprocess
import sys
import time

from entregable3 import BOOK,OUTPUT


if __name__=='__main__':
    path=OUTPUT/'scopus/catboost/reporte.json'
    deadline=time.monotonic()+7200
    while True:
        try:
            report=json.loads(path.read_text(encoding='utf-8'))
            if report['key']=='catboost':break
        except (FileNotFoundError,json.JSONDecodeError):pass
        if time.monotonic()>deadline:raise TimeoutError('CatBoost aún no terminó; revisar su log.')
        time.sleep(2)
    commands=[['resumen_scopus_e3.py'],['auditar_scopus_e3.py'],
        ['ejecutar_notebooks_scopus_e3.py','precalculo_catboost_scopus_e3.ipynb','precalculo_scopus_e3.ipynb']]
    for command in commands:
        print('Ejecutando:',command,flush=True)
        subprocess.run([sys.executable,*command],cwd=BOOK,check=True)
    print('Comparación, auditoría y notebooks completos.',flush=True)
