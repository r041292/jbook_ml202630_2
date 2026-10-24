"""Búsqueda reproducible de literatura para la matriz de novedad (cap. 4).

Consulta tres bases con API pública y registra, para cada cadena, el total que informa la
base y los primeros registros por relevancia (título, año, DOI/URL y resumen) para su
revisión manual. No inventa conteos: si una consulta falla, lo registra como fallo.

Bases: OpenAlex (título y resumen), arXiv (todos los campos) y Semantic Scholar
(búsqueda masiva con operadores booleanos). Fecha y hora de consulta en America/Bogota.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
OUT = HERE / 'salidas' / 'busqueda_literatura.json'
TOP = 25
BOGOTA = timezone(timedelta(hours=-5))

# id, familia, cadena OpenAlex/Semantic Scholar (booleana) y cadena arXiv.
STRINGS = [
    ('S1', 'KRR × problema (EN)',
     '"kernel ridge" AND ("student performance" OR "academic performance" OR "exam score" OR grade)',
     'all:"kernel ridge" AND (all:student OR all:academic OR all:grade)'),
    ('S2', 'KRR centrado (familia)',
     '"kernel ridge" AND (centering OR centred OR centered OR "mean-centered" OR intercept) AND target',
     'all:"kernel ridge" AND (all:centering OR all:centered OR all:intercept)'),
    ('S3', 'TN-KRR (familia)',
     '"truncated Newton" AND "kernel ridge"',
     'all:"truncated Newton" AND all:"kernel ridge"'),
    ('S4', 'TN-KRR / CG × problema',
     '"kernel ridge" AND ("conjugate gradient" OR "truncated Newton") AND (student OR academic OR education)',
     'all:"kernel ridge" AND all:"conjugate gradient" AND (all:student OR all:education)'),
    ('S5', 'GPR–XGBoost × problema',
     '"Gaussian process" AND (XGBoost OR "gradient boosting") AND ("student performance" OR "academic performance" OR grade)',
     'all:"Gaussian process" AND (all:XGBoost OR all:"gradient boosting") AND (all:student OR all:academic)'),
    ('S6', 'GPR–XGBoost (familia)',
     '"Gaussian process" AND XGBoost AND (residual OR stacking OR hybrid)',
     'all:"Gaussian process" AND all:XGBoost AND (all:residual OR all:stacking OR all:hybrid)'),
    ('S7', 'Problema: precálculo / nivelación',
     '(precalculus OR "placement test" OR ALEKS) AND ("machine learning" OR prediction) AND (grade OR exam OR performance)',
     '(all:precalculus OR all:ALEKS OR all:"placement test") AND (all:"machine learning" OR all:prediction)'),
    ('S8', 'Sinónimos en español',
     '("regresión ridge" OR "proceso gaussiano" OR "procesos gaussianos" OR kernel) AND ("rendimiento académico" OR "desempeño académico") AND (predicción OR "aprendizaje automático")',
     None),
]


def get(url, headers=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'jbook-e4-final/1.0', **(headers or {})})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode('utf-8')


def inverted_to_text(index):
    if not index:
        return ''
    words = sorted((p, w) for w, positions in index.items() for p in positions)
    return ' '.join(w for _, w in words)


def openalex(query):
    params = {'filter': f'title_and_abstract.search:{query}', 'per-page': TOP, 'sort': 'relevance_score:desc'}
    data = json.loads(get('https://api.openalex.org/works?' + urllib.parse.urlencode(params)))
    rows = [{'titulo': w.get('display_name'), 'anio': w.get('publication_year'), 'doi': w.get('doi'),
             'url': w.get('id'), 'resumen': inverted_to_text(w.get('abstract_inverted_index'))[:900]}
            for w in data['results']]
    return data['meta']['count'], rows


def arxiv(query):
    params = {'search_query': query, 'start': 0, 'max_results': TOP, 'sortBy': 'relevance'}
    root = ET.fromstring(get('https://export.arxiv.org/api/query?' + urllib.parse.urlencode(params)))
    ns = {'a': 'http://www.w3.org/2005/Atom', 'o': 'http://a9.com/-/spec/opensearch/1.1/'}
    total = int(root.find('o:totalResults', ns).text)
    rows = [{'titulo': ' '.join(e.find('a:title', ns).text.split()), 'anio': e.find('a:published', ns).text[:4],
             'doi': None, 'url': e.find('a:id', ns).text,
             'resumen': ' '.join(e.find('a:summary', ns).text.split())[:900]} for e in root.findall('a:entry', ns)]
    return total, rows


def semantic(query):
    # La búsqueda masiva admite «+» (AND), «|» (OR) y comillas; se traduce la cadena booleana.
    translated = query.replace(' AND ', ' + ').replace(' OR ', ' | ')
    params = {'query': translated, 'fields': 'title,year,externalIds,abstract,url'}
    for attempt in range(4):
        try:
            data = json.loads(get('https://api.semanticscholar.org/graph/v1/paper/search/bulk?' + urllib.parse.urlencode(params)))
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(8 * (attempt + 1))
    rows = [{'titulo': p.get('title'), 'anio': p.get('year'), 'doi': (p.get('externalIds') or {}).get('DOI'),
             'url': p.get('url'), 'resumen': (p.get('abstract') or '')[:900]} for p in (data.get('data') or [])[:TOP]]
    return data.get('total'), rows


def main():
    results = []
    for sid, family, boolean, arxiv_query in STRINGS:
        for base, function, query in [('OpenAlex', openalex, boolean), ('arXiv', arxiv, arxiv_query),
                                      ('Semantic Scholar', semantic, boolean)]:
            if query is None:
                continue
            stamp = datetime.now(BOGOTA).isoformat(timespec='seconds')
            try:
                total, rows = function(query)
                state = 'ok'
            except Exception as error:  # se registra el fallo, no se rellena la fila
                total, rows, state = None, [], f'fallo: {type(error).__name__}: {error}'
            results.append({'id': sid, 'familia': family, 'base': base, 'cadena': query, 'consulta': stamp,
                            'total': total, 'estado': state, 'registros': rows})
            print(sid, base, total, state[:60])
            time.sleep(3)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
