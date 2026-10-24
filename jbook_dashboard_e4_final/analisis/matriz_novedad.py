"""Matriz de novedad (Cuadro 2 de la guía) a partir de `salidas/busqueda_literatura.json`.

«Resultados» es el total que informa cada base. «Revisados» son los registros cuyo título
(y resumen, cuando parecía pertinente) se leyó: todos si la base devolvió 25 o menos; los
25 primeros por relevancia en otro caso. «Relevantes» y la observación son la valoración
manual registrada abajo (2026-10-24): un registro es relevante si aplica la familia del
modelo a la predicción de notas o rendimiento estudiantil, o si es un trabajo cercano de la
misma familia algorítmica (para la tabla de trabajos cercanos).
"""
import json

import pandas as pd

from comun import OUT

TOP = 25
# (id, base) -> (relevantes, observación). Valoración manual de títulos y resúmenes.
REVIEW = {
    ('S1', 'OpenAlex'): (2, 'Ahmed et al. (2022) usan KRR como comparador para la nota de Matemáticas de Ingeniería; '
                           'Cherfane et al. (2026) incluyen kernel ridge en un ensamble que predice el MCAT. Ninguno centra el objetivo.'),
    ('S1', 'arXiv'): (0, 'Teoría de KRR y aplicaciones ajenas (dosis, finanzas).'),
    ('S1', 'Semantic Scholar'): (2, 'Los mismos dos estudios cercanos que en OpenAlex.'),
    ('S2', 'OpenAlex'): (0, 'Centrado en otros sentidos (kernels condicionados, química); sin educación.'),
    ('S2', 'arXiv'): (1, 'Elkhalil et al. (2019) analizan la «centered KRR» (KRR con desplazamiento) en alta dimensión; teoría, sin aplicación educativa.'),
    ('S2', 'Semantic Scholar'): (0, 'Sin trabajos educativos ni de centrado del objetivo en KRR.'),
    ('S3', 'OpenAlex'): (2, 'Maalouf y Homouz (2014) proponen TN-KRR; Abdulla et al. (2022) lo aplican a porosidad de SS316L.'),
    ('S3', 'arXiv'): (0, 'Sin resultados.'),
    ('S3', 'Semantic Scholar'): (2, 'Los mismos dos trabajos que en OpenAlex.'),
    ('S4', 'OpenAlex'): (0, 'Sin resultados.'),
    ('S4', 'arXiv'): (0, 'Sin resultados.'),
    ('S4', 'Semantic Scholar'): (0, 'Sin resultados.'),
    ('S5', 'OpenAlex'): (2, 'Retno et al. (2024) usan GP y XGBoost por separado para clasificar notas finales; Shen y Shen (2026) comparan 18 algoritmos '
                           'de rendimiento académico. Ningún registro revisado describe un híbrido GPR–XGBoost.'),
    ('S5', 'arXiv'): (0, 'Sin resultados.'),
    ('S5', 'Semantic Scholar'): (0, 'Aplicaciones de ingeniería y salud; ninguna educativa.'),
    ('S6', 'OpenAlex'): (4, 'Híbridos GP–XGBoost en baterías (Hu et al., 2026), turbinas (Janani y Sasikala Reddy, 2025), '
                           'corrección de residuos en concreto (Rai et al., 2026) y pandeo de cascarones (De et al., 2026).'),
    ('S6', 'arXiv'): (1, 'De et al. (2026), el preprint de referencia del híbrido GPR–XGBoost.'),
    ('S6', 'Semantic Scholar'): (2, 'De et al. (2026) y un ensamble eólico con corrección de error por GP.'),
    ('S7', 'OpenAlex'): (3, 'Predicción de notas con pruebas de ubicación (Şen et al., 2012; Madison et al., 2014) y con un test de precálculo; '
                           'métodos estadísticos o de minería de datos, ninguno con KRR, TN-KRR ni GPR–XGBoost.'),
    ('S7', 'arXiv'): (0, 'Coincidencias por «ALEKS» y «prediction» en física y química.'),
    ('S7', 'Semantic Scholar'): (2, 'Estudios de rendimiento en cursos remediales y de matemáticas sin los modelos propuestos.'),
    ('S8', 'OpenAlex'): (2, 'Dos estudios en español de éxito académico con regresión logística, SVM, RF y MLP; sin KRR ni GPR–XGBoost.'),
    ('S8', 'Semantic Scholar'): (1, 'El mismo estudio peruano de 2022.'),
}


def main():
    data = json.loads((OUT / 'busqueda_literatura.json').read_text(encoding='utf-8'))
    rows = []
    for q in data:
        relevant, note = REVIEW[(q['id'], q['base'])]
        rows.append({'Cadena': q['id'], 'Familia': q['familia'], 'Base de datos': q['base'],
                     'Cadena de búsqueda': q['cadena'], 'Fecha de consulta': q['consulta'][:10],
                     'Resultados': q['total'], 'Revisados': min(q['total'], TOP), 'Relevantes': relevant,
                     'Observación': note})
    table = pd.DataFrame(rows)
    assert (table.Relevantes <= table.Revisados).all()
    table.to_csv(OUT / 'matriz_novedad.csv', index=False, encoding='utf-8')
    print(table[['Cadena', 'Base de datos', 'Resultados', 'Revisados', 'Relevantes']].to_string())


if __name__ == '__main__':
    main()
