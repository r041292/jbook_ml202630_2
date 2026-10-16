import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
p=Path(__file__).parent / (sys.argv[1] if len(sys.argv) > 1 else 'precalculo_entregable3.ipynb')
nb=nbformat.read(p, as_version=4)
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
NotebookClient(nb, km=km, timeout=180, allow_errors=False, resources={'metadata':{'path':str(p.parent.resolve())}}).execute()
nbformat.write(nb,p)
print('Notebook E3 ejecutado sin errores.')
