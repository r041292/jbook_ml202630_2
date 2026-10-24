"""Genera `references.bib` a partir de DOI comprobados en Crossref.

Cada DOI se resuelve con negociación de contenido (BibTeX) en doi.org y se verifica
contra la API de Crossref (título y año). Las obras sin DOI (JMLR, NeurIPS, actas sin
registro, arXiv) se escriben a mano con su URL estable y se marcan en
`salidas/bibliografia_verificacion.csv` como «sin DOI». Requiere conexión a internet;
el build del libro NO la requiere, porque lee el `.bib` ya versionado.
"""
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIB = HERE.parent / 'references.bib'
LOG = HERE / 'salidas' / 'bibliografia_verificacion.csv'

# clave -> DOI. Las 15 referencias de la guía van primero; después, las del proyecto.
DOIS = {
    'delong1988': '10.2307/2531595',
    'nadeau2003': '10.1023/A:1024068626366',
    'dietterich1998': '10.1162/089976698300017197',
    'diebold1995': '10.1080/07350015.1995.10524599',
    'harvey1997': '10.1016/S0169-2070(96)00719-4',
    'giacomini2006': '10.1111/j.1468-0262.2006.00718.x',
    'clark2007': '10.1016/j.jeconom.2006.05.023',
    'hansen2011': '10.3982/ECTA5771',
    'hansen2005': '10.1198/073500105000000063',
    'politis1994': '10.1080/01621459.1994.10476870',
    'akiba2019': '10.1145/3292500.3330701',
    # Proyecto
    'eckhard2014': '10.1364/JOSAA.31.000541',
    'abdulla2022': '10.3390/app12094252',
    'maalouf2014': '10.1016/j.knosys.2014.08.012',
    'smola2004': '10.1023/B:STCO.0000035301.49549.88',
    'chen2016': '10.1145/2939672.2939785',
    'breiman2001': '10.1023/A:1010933404324',
    'hoerl1970': '10.1080/00401706.1970.10488634',
    'tibshirani1996': '10.1111/j.2517-6161.1996.tb02080.x',
    'altman1992': '10.1080/00031305.1992.10475879',
    'wolpert1992': '10.1016/S0893-6080(05)80023-1',
    'hestenes1952': '10.6028/jres.049.044',
    'rasmussen2006': '10.7551/mitpress/3206.001.0001',
    'efron1987': '10.1080/01621459.1987.10478410',
    'cliff1993': '10.1037/0033-2909.114.3.494',
    'benjamini1995': '10.1111/j.2517-6161.1995.tb02031.x',
    'friedman1937': '10.1080/01621459.1937.10503522',
    'wilcoxon1945': '10.2307/3001968',
    'steininger2021': '10.1007/s10994-021-06023-5',
    'zuhlke2025': '10.1007/s10994-024-06704-x',
    'lau2023': '10.1007/s10994-023-06488-6',
    # Trabajos cercanos hallados en la búsqueda del cap. 4 (analisis/busqueda_literatura.py)
    'ahmed2022': '10.3390/su141711070',
    'cherfane2026': '10.2196/94197',
    'sen2012': '10.1016/j.eswa.2012.02.112',
    'madison2014': '10.1080/10511970.2014.921653',
    'hu2026': '10.1149/1945-7111/ae4899',
    'janani2025': '10.58482/ijersem.v1i3.1',
    'rai2026': '10.1061/jmcee7.mteng-23555',
    'retno2024': '10.1109/siml61815.2024.10578074',
    'shen2026': '10.21203/rs.3.rs-10184303/v1',
    'bergstra2012': None,  # JMLR, sin DOI (manual)
}

MANUAL = r"""
@article{demsar2006,
  author = {Dem{\v{s}}ar, Janez},
  title = {Statistical Comparisons of Classifiers over Multiple Data Sets},
  journal = {Journal of Machine Learning Research},
  volume = {7},
  pages = {1--30},
  year = {2006},
  url = {https://jmlr.org/papers/v7/demsar06a.html}
}

@article{benavoli2017,
  author = {Benavoli, Alessio and Corani, Giorgio and Dem{\v{s}}ar, Janez and Zaffalon, Marco},
  title = {Time for a Change: a Tutorial for Comparing Multiple Classifiers Through {B}ayesian Analysis},
  journal = {Journal of Machine Learning Research},
  volume = {18},
  number = {77},
  pages = {1--36},
  year = {2017},
  url = {https://jmlr.org/papers/v18/16-305.html}
}

@inproceedings{romano2006,
  author = {Romano, Jeanine and Kromrey, Jeffrey D. and Coraggio, Jesse and Skowronek, Jeff},
  title = {Appropriate statistics for ordinal level data: Should we really be using t-test and {C}ohen's d for evaluating group differences on the {NSSE} and other surveys?},
  booktitle = {Annual Meeting of the Florida Association of Institutional Research},
  year = {2006}
}

@inproceedings{lundberg2017,
  author = {Lundberg, Scott M. and Lee, Su-In},
  title = {A Unified Approach to Interpreting Model Predictions},
  booktitle = {Advances in Neural Information Processing Systems},
  volume = {30},
  year = {2017},
  url = {https://arxiv.org/abs/1705.07874}
}

@article{bergstra2012,
  author = {Bergstra, James and Bengio, Yoshua},
  title = {Random Search for Hyper-Parameter Optimization},
  journal = {Journal of Machine Learning Research},
  volume = {13},
  pages = {281--305},
  year = {2012},
  url = {https://jmlr.org/papers/v13/bergstra12a.html}
}

@article{pedregosa2011,
  author = {Pedregosa, Fabian and Varoquaux, Ga{\"e}l and Gramfort, Alexandre and Michel, Vincent and Thirion, Bertrand and Grisel, Olivier and others},
  title = {Scikit-learn: Machine Learning in {P}ython},
  journal = {Journal of Machine Learning Research},
  volume = {12},
  pages = {2825--2830},
  year = {2011},
  url = {https://jmlr.org/papers/v12/pedregosa11a.html}
}

@misc{de2026,
  author = {De, Budhaditya and Majumder, Rohan and Dutta, Devasmit and Gupta, Aman Deep and Mishra, Sudib Kumar},
  title = {A Hybrid {G}aussian Process-Extreme Gradient Boosting Machine Learning Framework for Robust Knockdown Factor Prediction and Reliability-Based Design of Thin Spherical Shell Caps},
  year = {2026},
  howpublished = {Preprint arXiv:2610.15862},
  url = {https://arxiv.org/abs/2610.15862}
}

@misc{elkhalil2019,
  author = {Elkhalil, Khalil and Kammoun, Abla and Zhang, Xiangliang and Alouini, Mohamed-Slim and Al-Naffouri, Tareq},
  title = {Risk Convergence of Centered Kernel Ridge Regression with Large Dimensional Data},
  year = {2019},
  howpublished = {Preprint arXiv:1904.09212},
  url = {https://arxiv.org/abs/1904.09212}
}

@article{holm1979,
  author = {Holm, Sture},
  title = {A Simple Sequentially Rejective Multiple Test Procedure},
  journal = {Scandinavian Journal of Statistics},
  volume = {6},
  number = {2},
  pages = {65--70},
  year = {1979},
  url = {https://www.jstor.org/stable/4615733}
}
"""


def fetch(url, accept):
    request = urllib.request.Request(url, headers={'Accept': accept, 'User-Agent': 'jbook-e4-final (mailto:none)'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read().decode('utf-8')


# Campos que el registro de Crossref no trae (verificados en la página del editor).
MISSING = {'hansen2011': 'title={The Model Confidence Set}, author={Hansen, Peter R. and Lunde, Asger and Nason, James M.}, '}


def rekey(bibtex, key):
    bibtex = re.sub(r'^@(\w+)\{[^,]*,', lambda m: f'@{m.group(1)}{{{key}, {MISSING.get(key, "")}', bibtex.strip(), count=1)
    # Crossref escapa «&» como entidad HTML; BibTeX necesita «\&».
    return bibtex.replace('&amp;', r'\&')


def main():
    entries, log = [], []
    for key, doi in DOIS.items():
        if doi is None:
            continue
        try:
            meta = json.loads(fetch(f'https://api.crossref.org/works/{urllib.parse.quote(doi)}', 'application/json'))['message']
            bib = rekey(fetch(f'https://doi.org/{doi}', 'application/x-bibtex; charset=utf-8'), key)
        except urllib.error.HTTPError as error:
            # Un DOI que Crossref no reconoce no entra al .bib: se registra y se corrige a mano.
            log.append({'clave': key, 'doi': doi, 'estado': f'No encontrado en Crossref ({error.code})',
                        'titulo_crossref': '', 'anio': '', 'revista': ''})
            print(f'{key}: {doi} no encontrado ({error.code})')
            continue
        year = (meta.get('issued', {}).get('date-parts') or [[None]])[0][0]
        log.append({'clave': key, 'doi': doi, 'estado': 'DOI comprobado en Crossref',
                    'titulo_crossref': (meta.get('title') or [''])[0], 'anio': year,
                    'revista': (meta.get('container-title') or [''])[0]})
        entries.append(bib)
        time.sleep(0.4)
    for match in re.finditer(r'@\w+\{(\w+),', MANUAL):
        log.append({'clave': match.group(1), 'doi': '', 'estado': 'Sin DOI · entrada manual con URL/fuente estable',
                    'titulo_crossref': '', 'anio': '', 'revista': ''})
    BIB.write_text('% Generado por analisis/bibliografia.py. DOI comprobados en Crossref.\n\n'
                   + '\n\n'.join(entries) + '\n' + MANUAL, encoding='utf-8')
    with LOG.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(log[0]))
        writer.writeheader()
        writer.writerows(log)
    print(f'{len(log)} referencias; {sum(1 for r in log if r["doi"])} con DOI comprobado.')


if __name__ == '__main__':
    import urllib.parse  # noqa: F401  (usado en main)
    main()
