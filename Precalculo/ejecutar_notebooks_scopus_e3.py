"""Ejecutar los notebooks nuevos con el Python del venv compartido."""
import argparse
import os
import uuid

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

from entregable3 import BOOK


def execute(name):
    runtime=BOOK/'modelos_preentrenados/scopus/jupyter_runtime'
    runtime.mkdir(parents=True,exist_ok=True)
    os.environ['JUPYTER_RUNTIME_DIR']=str(runtime)
    os.environ['IPYTHONDIR']=str(runtime/'ipython')
    path=BOOK/name
    notebook=nbformat.read(path,as_version=4)
    km=KernelManager(connection_file=str(runtime/f'kernel_{uuid.uuid4().hex}.json'))
    km.kernel_spec.argv=[str(BOOK/'venv/Scripts/python.exe'),'-m','ipykernel_launcher',
                        '-f','{connection_file}']
    try:
        NotebookClient(notebook,km=km,timeout=600,resources={'metadata':{'path':str(BOOK)}}).execute()
        nbformat.validate(notebook)
        nbformat.write(notebook,path)
        print(f'Ejecutado: {name}',flush=True)
    finally:
        if km.has_kernel:km.shutdown_kernel(now=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('notebooks',nargs='+')
    for name in p.parse_args().notebooks:execute(name)
