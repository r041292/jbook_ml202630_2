"""Create only the new TR-KRR notebook, preserving executed notebooks."""
import argparse

import nbformat as nbf

from entregable3 import BOOK


def create(force=False):
    path = BOOK / 'precalculo_tn_krr_e3.ipynb'
    if path.exists() and not force:
        raise FileExistsError(f'{path} ya existe; usa --force para reemplazarlo.')
    cells = [
        nbf.v4.new_markdown_cell(
            '# E3 — Truncated Newton Kernel Ridge Regression\n\n'
            'Implementación separada del KRR de solución exacta. El artículo '
            '[aplicado de Abdulla et al. (2022)](https://doi.org/10.3390/app12094252) '
            'remite al método TR-KRR de [Maalouf y Homouz (2014)]'
            '(https://doi.org/10.1016/j.knosys.2014.08.012).'),
        nbf.v4.new_markdown_cell(
            '## Procedimiento\n\n'
            'El estimador resuelve `(K + alpha I) a = y` para el kernel RBF '
            '`exp(-gamma ||x-z||²)` con gradiente conjugado lineal desde `a=0`. '
            'Usa máximo 200 iteraciones, tolerancia de norma residual 0,5 y '
            'terminación después de 25 iteraciones sin mejora, como publica '
            'Maalouf y Homouz. El artículo no precisa la métrica de no mejora '
            'ni el vector inicial: usamos residuo L2 y `a=0`. No transforma `y`.\n\n'
            'El protocolo de datos es la adaptación E3: train/test temporal '
            'canónico, folds agrupados por estudiante, pipeline ajustado dentro '
            'de cada fit, grilla alpha/gamma de 35 candidatos y selección por '
            'RMSE anidada 5×5. Test no elige parámetros. Esto implementa el '
            'solver del paper, sin afirmar una réplica de su experimento.'),
        nbf.v4.new_code_cell(
            'from pathlib import Path\nimport sys\n'
            "BOOK = Path.cwd() if (Path.cwd() / 'evaluar_tn_krr_e3.py').exists() "
            "else Path.cwd() / 'Precalculo'\n"
            'sys.path.insert(0, str(BOOK.resolve()))\n'
            'import pandas as pd\n'
            'from evaluar_tn_krr_e3 import run, ROOT\n'
            'from tn_krr_e3 import TruncatedNewtonKernelRidgeRegressor\n'
            'report = run()\n'
            'display(pd.DataFrame(report["cv"]).round(6))\n'
            'print("Parámetros finales:", report["best_params"])'),
        nbf.v4.new_markdown_cell('## Test temporal y diagnóstico del optimizador'),
        nbf.v4.new_code_cell(
            'display(pd.DataFrame([report["test"]]).round(6))\n'
            'display(pd.DataFrame(report["fold_audit"]))\n'
            'grid = pd.read_csv(ROOT / "grid_final.csv")\n'
            'display(grid.groupby(["alpha", "gamma"])[\n'
            '    ["RMSE", "cg_iterations", "cg_residual_norm", "cg_converged"]\n'
            '].mean().sort_values("RMSE").head(10))'),
        nbf.v4.new_markdown_cell(
            'El informe separa la media de los folds externos, OOF agrupado y test. '
            'Un solver que se detenga por máximo de iteraciones o por no mejora '
            'devuelve la aproximación TR-CG y queda identificado en la auditoría.'),
    ]
    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata['kernelspec'] = {
        'display_name': 'Python (Precalculo/venv)', 'language': 'python', 'name': 'python3'}
    notebook.metadata['language_info'] = {'name': 'python'}
    nbf.write(notebook, path)
    print(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Replace this notebook only.')
    create(parser.parse_args().force)
