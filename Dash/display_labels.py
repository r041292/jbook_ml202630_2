"""Etiquetas de presentación; los códigos del modelo se conservan intactos."""
import re

COURSES = {'MAT1011': 'Álgebra y Trigonometría', 'MAT1100': 'Cálculo I (ANEC)',
           'MAT1101': 'Cálculo I', 'MAT4190': 'Matemáticas Fundamentales'}


def course_text(value):
    if not isinstance(value, str):
        return value
    return re.sub(r'MAT(?:1011|1100|1101|4190)(?! - )',
                  lambda match: match[0] + ' - ' + COURSES[match[0]], value)


def display_tree(value):
    """También transforma leyendas, ticks y datos del hover de Plotly."""
    if isinstance(value, dict):
        return {k: display_tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [display_tree(v) for v in value]
    if hasattr(value, 'dtype') and value.dtype.kind in 'OUS':
        return display_tree(value.tolist())
    return course_text(value)
