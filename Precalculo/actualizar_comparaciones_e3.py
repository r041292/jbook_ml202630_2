"""Actualiza el panorama E3 de 26 modelos desde reportes agregados, sin entrenar.

Conserva las familias de inferencia publicadas; no calcula contrastes nuevos.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


DESCRIPTIONS = {
    "SVR RBF": "SVR con kernel RBF; no linealidad mediante distancias entre observaciones.",
    "TabICLv2": "Modelo tabular preentrenado mediante aprendizaje en contexto.",
    "TabPFN 2.5 original": "TabPFN 2.5 preentrenado, sin ajuste adicional de pesos.",
    "LinXGBoost (hojas completas E3)": "Boosting con hojas Ridge sobre 67 columnas; port independiente con cortes cuantílicos y diferencias numéricas documentadas.",
    "TabPFN 2.5 fine-tuned": "TabPFN 2.5 con pesos ajustados en train; sin nueva OOF independiente.",
    "Kernel Ridge RBF": "Regresión Ridge en kernel RBF mediante solución exacta.",
    "CatBoost": "Boosting de árboles con tratamiento de variables categóricas.",
    "XGBoost": "XGBoost de referencia con categorías nativas y búsqueda de parámetros en train.",
    "TCR-XGBoost": "Adaptación de TCR-XGBoost al protocolo E3.",
    "TabFM 1.0.0 (PyTorch CPU, 32 vistas)": "Modelo tabular preentrenado TabFM 1.0.0, inferencia CPU con 32 vistas.",
    "XGBoost ampliado (gbtree)": "Control XGBoost con una búsqueda de hiperparámetros ampliada.",
    "RaFFLE": "RaFFLE v0.0.5; evaluación completa, wrapper nativo sin serialización joblib.",
    "DenseWeight-XGBoost": "XGBoost con pesos según la rareza del objetivo, estimada dentro de cada fit.",
    "Ridge": "Regresión lineal con penalización L2.",
    "Lasso": "Regresión lineal con penalización L1.",
    "DART-XGBoost": "XGBoost con dropout de árboles durante el entrenamiento.",
    "KNN": "Regresión mediante vecinos cercanos.",
    "HRT-Boost": "Adaptación de HRT-Boost al protocolo E3.",
    "logicDT propio (adaptado)": "Adaptación propia de logicDT; resultado de la implementación evaluada.",
    "SVM lineal": "SVR lineal usado como referencia histórica de E3.",
    "Random Forest": "Bosque de árboles de regresión.",
    "GPR–XGBoost (OOF agrupado)": "Combinación GPR–XGBoost con construcción OOF agrupada por estudiante.",
    "RIM (port E3)": "Port de RIM adaptado al conjunto y protocolo E3.",
    "XBART (GFR)": "Variante XBART GFR de stochtree; alcance limitado a esa implementación.",
    "coPILOT": "coPILOT a partir del código de los autores.",
    "Dummy media": "Referencia que predice la media de train.",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path, value):
    path.write_text(json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(clean(rows))


def significance(delta, probability, improvement="lower"):
    if probability is None:
        return "No evaluada en esta familia"
    if probability >= 0.05:
        return "No significativa"
    better = delta < 0 if improvement == "lower" else delta > 0
    return "Mejora significativa" if better else "Deterioro significativo"


def bootstrap_history(output):
    """Congela la última comparación de 22 antes de reemplazar su vista actual."""
    for folder, filename in [("resumen_completo", "resumen.json"), ("validacion_r2", "reporte.json"), ("validacion_r2", "folds_r2.csv"), ("validacion_r2", "contrastes_r2_vs_xgboost.csv")]:
        source = output / folder / filename
        target = output / folder / "historico_22" / filename
        if target.exists():
            continue
        if load(output / folder / ("resumen.json" if folder == "resumen_completo" else "reporte.json"))["model_count"] != 22:
            raise ValueError("Se necesita el corte histórico de 22 modelos para inicializar las fuentes.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def build(book):
    output = book / "resultados" / "e3"
    bootstrap_history(output)
    paths = [output / "resumen_completo/historico_22/resumen.json",
             output / "validacion_r2/historico_22/reporte.json",
             output / "validacion_r2/historico_22/folds_r2.csv",
             output / "linxgboost/reporte.json", output / "xgboost_variantes/reporte.json",
             output / "xgboost_variantes/fold_metrics.csv"]
    history, r2_history = load(paths[0]), load(paths[1])
    lin, variants = load(paths[3]), load(paths[4])
    ranking = lin["ranking_global_26"]
    recent = [(model, "Holm12", "p_Holm_family_12", variants["contrasts"]) for model in variants["models"].values()]
    recent.append((lin["model"], "Holm7", "p_Holm_family_7", lin["contrasts"]))
    historical = {row["Modelo"]: row for row in history["models"]}
    r2_old = {row["Modelo"]: row for row in r2_history["models"]}
    new = {item[0]["model"]: item for item in recent}
    svm_rmse = float(next(row["RMSE_test"] for row in ranking if row["Modelo"] == "SVM lineal"))
    xgb_rmse = float(next(row["RMSE_test"] for row in ranking if row["Modelo"] == "XGBoost"))
    svm_r2, xgb_r2 = r2_old["SVM lineal"]["R2_test"], r2_old["XGBoost"]["R2_test"]
    rows, r2_rows = [], []
    cv = {row["Modelo"]: dict(row) for row in r2_history["cv"]}
    for index, item in enumerate(ranking, 1):
        name, rmse = item["Modelo"], float(item["RMSE_test"])
        row = dict(historical.get(name, {}))
        row.update(rango_RMSE=index, Modelo=name, RMSE_test=rmse,
                   delta_RMSE_vs_SVM=rmse-svm_rmse, delta_RMSE_vs_XGBoost=rmse-xgb_rmse,
                   descripcion=DESCRIPTIONS[name], estado="Evaluado; test temporal exploratorio")
        r2_row = dict(r2_old.get(name, {}))
        if name in new:
            report, family, p_column, contrasts = new[name]
            pairs = [pair for pair in contrasts if pair["Modelo"] == name and pair["Referencia"] == "XGBoost"]
            rmse_pair = next(pair for pair in pairs if pair["metrica"] == "RMSE")
            r2_pair = next(pair for pair in pairs if pair["metrica"] == "R²")
            row.update(R2_test=report["test"]["R²"], Referencia_inferencia="XGBoost",
                       familia_principal=family, p_bilateral_referencia=rmse_pair["p_bilateral"],
                       p_Holm_familia_principal=rmse_pair[p_column],
                       significancia_ajustada=significance(rmse_pair["diferencia_candidato_menos_referencia"], rmse_pair[p_column]))
            r2_row.update(Modelo=name, Referencia="XGBoost", R2_test=report["test"]["R²"],
                          delta_R2=r2_pair["diferencia_candidato_menos_referencia"],
                          p_bilateral=r2_pair["p_bilateral"],
                          IC95_delta_inferior=r2_pair["IC_2.5%"], IC95_delta_superior=r2_pair["IC_97.5%"],
                          familia_principal=family, p_Holm_familia_principal=r2_pair[p_column],
                          significancia_ajustada=significance(r2_pair["diferencia_candidato_menos_referencia"], r2_pair[p_column], "higher"))
            # Los contrastes históricos vs SVM no se inventan para las variantes.
            svm_pairs = [pair for pair in contrasts if pair["Modelo"] == name and pair["Referencia"] == "SVM lineal" and pair["metrica"] == "RMSE"]
            row["p_bilateral"] = svm_pairs[0]["p_bilateral"] if svm_pairs else None
            row["significancia_sin_correccion"] = significance(row["delta_RMSE_vs_SVM"], row["p_bilateral"])
            row["significancia_Holm_vs_SVM_21"] = "No evaluada en esta familia"
            row["significancia_Holm_global_55"] = "No evaluada en esta familia"
            r2_row["significancia_sin_correccion"] = significance(r2_row["delta_R2"], r2_row["p_bilateral"], "higher")
            r2_row["significancia_Holm_vs_SVM_21"] = "No evaluada en esta familia"
            r2_row["significancia_Holm_global_55"] = "No evaluada en esta familia"
            row["p_bilateral_vs_XGBoost"] = rmse_pair["p_bilateral"]
            row["p_Holm_variantes_12_vs_XGBoost" if family == "Holm12" else "p_Holm_LinXGBoost_family_7_vs_XGBoost"] = rmse_pair[p_column]
            score = next(score for score in report["cv"] if score["metrica"] == "R²")
            cv[name] = {"Modelo": name, "R2_media_CV": score["media_cv"], "R2_SD_CV_ddof0": score["sd_cv"],
                        "R2_OOF_reunido": score["OOF_agrupado"], "R2_test": report["test"]["R²"],
                        "CV_estado": "5 folds externos por estudiante"}
        else:
            row.update(R2_test=r2_row["R2_test"], Referencia_inferencia="SVM lineal", familia_principal="Holm55",
                       p_bilateral_referencia=row.get("p_bilateral"), p_Holm_familia_principal=row.get("p_Holm_global_55"),
                       significancia_ajustada="Referencia" if name == "SVM lineal" else row["significancia_Holm_global_55"])
            r2_row.update(familia_principal="Holm55", p_Holm_familia_principal=r2_row.get("p_Holm_global_55"),
                          significancia_ajustada="Referencia" if name == "SVM lineal" else r2_row["significancia_Holm_global_55"])
        r2_row.update(rango_RMSE=index, delta_R2_vs_SVM=r2_row["R2_test"]-svm_r2,
                      delta_R2_vs_XGBoost=r2_row["R2_test"]-xgb_r2)
        rows.append(row)
        r2_rows.append(r2_row)
    names = [row["Modelo"] for row in rows]
    if len(names) != 26 or len(set(names)) != 26 or set(names) != set(DESCRIPTIONS):
        raise ValueError("El inventario no coincide con los 26 modelos evaluados.")
    if [row["RMSE_test"] for row in rows] != sorted(row["RMSE_test"] for row in rows):
        raise ValueError("Ranking RMSE desordenado.")
    variance = xgb_rmse**2/(1-xgb_r2)
    if any(not math.isclose(row["R2_test"], 1-row["RMSE_test"]**2/variance, abs_tol=1e-10) for row in rows):
        raise ValueError("RMSE y R² no corresponden al mismo test.")

    # Detalle por fold: solo métricas agregadas, sin IDs ni predicciones individuales.
    fold_rows = read_csv(paths[2])
    fold_sizes = {int(item["fold"]): int(item["validation_rows"]) for item in lin["model"]["fold_audit"]}
    if len(fold_sizes) != 5 or sum(fold_sizes.values()) != 1309:
        raise ValueError("Partición externa inesperada.")
    for report in variants["models"].values():
        if {int(item["fold"]): int(item["validation_rows"]) for item in report["fold_audit"]} != fold_sizes:
            raise ValueError("Las variantes no comparten los tamaños de fold canónicos.")
    extra_folds = read_csv(paths[5]) + lin["model"]["fold_metrics"]
    for item in extra_folds:
        fold = int(item["Fold"])
        fold_rows.append({"Modelo": item["Modelo"], "Fold": fold,
                          "R2_validacion_externa": float(item["R²"]), "n": fold_sizes[fold]})
    if len(fold_rows) != 125 or len({(row["Modelo"], int(row["Fold"])) for row in fold_rows}) != 125:
        raise ValueError("Se esperaban 125 resultados de fold únicos.")
    for name in names:
        values = [float(row["R2_validacion_externa"]) for row in fold_rows if row["Modelo"] == name]
        if not values:
            if name != "TabPFN 2.5 fine-tuned":
                raise ValueError(f"Faltan folds: {name}")
            continue
        mean = sum(values)/len(values)
        sd = math.sqrt(sum((value-mean)**2 for value in values)/len(values))
        if len(values) != 5 or not math.isclose(mean, float(cv[name]["R2_media_CV"]), abs_tol=1e-10) or not math.isclose(sd, float(cv[name]["R2_SD_CV_ddof0"]), abs_tol=1e-10):
            raise ValueError(f"CV agregada no coincide con folds: {name}")
    position = {name: index for index, name in enumerate(names)}
    fold_rows.sort(key=lambda row: (position[row["Modelo"]], int(row["Fold"])))

    # La familia queda junto a cada p ajustado; RMSE/R² comparten la prueba SSE.
    contrast_rows = []
    for folder, family, field in [("svr_rbf_raffle", "Holm55", "p_Holm_global_55"), ("xgboost_variantes", "Holm12", "p_Holm_family_12"), ("linxgboost", "Holm7", "p_Holm_family_7")]:
        path = output / folder / "contrastes_pareados.csv"
        paths.append(path)
        for pair in read_csv(path):
            if pair["metrica"] not in ("RMSE", "R²"):
                continue
            contrast_rows.append({"Modelo": pair["Modelo"], "Referencia": pair["Referencia"], "metrica": pair["metrica"],
                                  "diferencia_candidato_menos_referencia": float(pair["diferencia_candidato_menos_referencia"]),
                                  "IC_2.5%": float(pair["IC_2.5%"]), "IC_97.5%": float(pair["IC_97.5%"]),
                                  "p_bilateral": float(pair["p_bilateral"]), "familia_ajuste": family,
                                  "p_ajustado": float(pair[field]), "significativa_al_5%": float(pair[field]) < .05,
                                  "fuente": str(path.relative_to(book)).replace("\\", "/")})
    historical_contrasts = output / "validacion_r2/historico_22/contrastes_r2_vs_xgboost.csv"
    paths.append(historical_contrasts)
    for pair in read_csv(historical_contrasts):
        contrast_rows.append({"Modelo": pair["Modelo"], "Referencia": pair["Referencia"], "metrica": "R²",
                              "diferencia_candidato_menos_referencia": float(pair["delta_R2"]),
                              "IC_2.5%": float(pair["IC95_delta_inferior"]), "IC_97.5%": float(pair["IC95_delta_superior"]),
                              "p_bilateral": float(pair["p_bilateral"]), "familia_ajuste": "Holm55",
                              "p_ajustado": float(pair["p_Holm_global_55"]),
                              "significativa_al_5%": float(pair["p_Holm_global_55"]) < .05,
                              "fuente": str(historical_contrasts.relative_to(book)).replace("\\", "/")})
    paths.append(book / "actualizar_comparaciones_e3.py")
    provenance = {str(path.relative_to(book)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    common = {"model_count": 26, "training_performed": False, "new_statistical_tests_performed": False,
              "partition": r2_history["partition"], "permutations": r2_history["permutations"],
              "bootstrap": r2_history["bootstrap"], "seed": r2_history["seed"],
              "hyperparameter_selection": r2_history["hyperparameter_selection"],
              "statistical_families": {"Holm55": "Familia histórica de 22 modelos; 21 contrastes vs SVM y contrastes suplementarios.",
                                       "Holm12": "12 contrastes de las tres variantes XGBoost.",
                                       "Holm7": "7 contrastes de LinXGBoost."},
              "caveat": "Test 202530 consultado en rondas anteriores; resultados exploratorios. No rechazar H0 no demuestra equivalencia.",
              "generator": "actualizar_comparaciones_e3.py", "sources_sha256": provenance}
    write_csv(output / "resumen_completo/modelos.csv", rows)
    write_csv(output / "linxgboost/ranking_global_26_modelos.csv", rows)
    write_csv(output / "resumen_completo/contrastes_actuales.csv", contrast_rows)
    write_json(output / "resumen_completo/resumen.json", {**common, "models": rows})
    write_csv(output / "validacion_r2/modelos_r2.csv", r2_rows)
    write_csv(output / "validacion_r2/validacion_cruzada_r2.csv", [cv[name] for name in names])
    write_csv(output / "validacion_r2/folds_r2.csv", fold_rows)
    write_csv(output / "validacion_r2/contrastes_r2_vs_xgboost.csv", [row for row in contrast_rows if row["metrica"] == "R²" and row["Referencia"] == "XGBoost"])
    write_json(output / "validacion_r2/reporte.json", {**common, "models": r2_rows, "cv": [cv[name] for name in names], "fold_evaluations": 125})
    table = ["| Puesto | Modelo | RMSE test | R² test | ΔRMSE vs XGBoost |", "|---:|---|---:|---:|---:|"]
    table += [f"| {row['rango_RMSE']} | {row['Modelo']} | {row['RMSE_test']:.6f} | {row['R2_test']:.6f} | {row['delta_RMSE_vs_XGBoost']:+.6f} |" for row in rows]
    note = """# Panorama actual de los 26 modelos — Entregable 3

Ranking descriptivo por RMSE en el mismo test temporal 202530 (188 estudiantes).
Se mantienen los datos reales sin aumentación, 15 predictores y objetivo `nota_primer_parcial`.
Train tiene 1309 filas de 1293 estudiantes. El preprocesamiento y la selección
de parámetros se realizan dentro de train con validación agrupada por estudiante.

Los 26 incluyen 22 modelos históricos, tres variantes XGBoost y LinXGBoost.
Las corridas LinXGBoost supersedidas y el diagnóstico preliminar de stacking quedan fuera.

""" + "\n".join(table) + """

## Conclusiones y alcance

SVR RBF conserva el menor RMSE (0.892225) y el mayor R² (0.471418).
Su reducción puntual de RMSE frente a XGBoost es 0.014049 (1.55%). Frente a
TabICLv2, ΔRMSE=-0.005590, IC95% [-0.025163; 0.014880] y Holm55=1.000:
el primer puesto no acredita superioridad estadística sobre el segundo.

LinXGBoost queda cuarto (RMSE 0.899069). Frente a XGBoost, ΔRMSE=-0.007205,
IC95% [-0.036278; 0.021475], p=0.62662 y Holm7=1.000. Tampoco se distingue
significativamente de SVR RBF ni TabICLv2. Su RMSE OOF (0.845385) supera
al de XGBoost original (0.814822), por lo que no demuestra una mejora consistente.
La implementación independiente usa 67 columnas, 12 cuantiles para los cortes
y diferencias numéricas al puntuar candidatos descritas en [su reporte](../linxgboost/resumen.md).
Las corridas previas de RMSE 1.012583 y 1.017309 están supersedidas.

XGBoost original ocupa el puesto 8. La búsqueda ampliada, DenseWeight y DART
quedan en los puestos 11, 13 y 16, respectivamente: ninguna reduce su RMSE test
ni demuestra una mejora ajustada. RaFFLE queda 12 y TabFM 10.
Para la preferencia de evitar deep learning, SVR RBF es el líder puntual;
LinXGBoost es la modificación metodológica reciente mejor situada, sin mejora significativa demostrada.

## Interpretación de los CSV y la inferencia

Los contrastes de los reportes usan permutación pareada de SSE por estudiante
con 99.999 reasignaciones y bootstrap pareado con 10.000 réplicas, semilla 42.
Esta consolidación reutiliza esas pruebas sin calcular otras nuevas.

- [modelos.csv](modelos.csv) integra los 26, RMSE/R², deltas, descripciones,
  referencia inferencial y p ajustado de la familia correspondiente.
- [contrastes_actuales.csv](contrastes_actuales.csv) reúne los contrastes
  publicados para SVR/RaFFLE, variantes XGBoost y LinXGBoost, además de los cuatro
  contrastes históricos R² Scopus–XGBoost, con referencia,
  IC95%, familia, p bruto, p ajustado y fuente. No es una matriz de todos los pares.
- Holm55 conserva la familia histórica; Holm12 corrige los 12 pares de las
  variantes y Holm7 los siete pares de LinXGBoost. No se ha calculado un Holm
  global único para los 26. Los p ajustados de familias distintas no se comparan
  como una escala de rendimiento.
- En `modelos.csv`, `p_bilateral` y las columnas históricas Holm21/Holm55 son
  frente a SVM lineal. `Referencia_inferencia` identifica el comparador de
  `p_bilateral_referencia`, `p_Holm_familia_principal` y `significancia_ajustada`.
  Una celda vacía significa no disponible o no perteneciente a esa familia, nunca p=0.
- RMSE y R² comparten SSE sobre las mismas observaciones y no son evidencia independiente.
  Los IC95% son marginales, no intervalos simultáneos corregidos por multiplicidad.
- El test ya fue consultado en varias rondas. El ranking y los contrastes
  son exploratorios; no rechazar una diferencia no demuestra equivalencia.
  Un nuevo test temporal permitiría confirmar las mejoras sin esa reutilización.

[Validación R², CV y folds](../validacion_r2/resumen.md).
Los reportes de 18, 22 y 25 modelos conservan el contexto de cada etapa.
Las fuentes de 22 de este resumen se conservan en `historico_22/`.
Para regenerar la vista actual sin entrenar: `python actualizar_comparaciones_e3.py`.
"""
    (output / "resumen_completo/resumen.md").write_text(note, encoding="utf-8")
    r2_note = """# Validación actual con R² — 26 modelos E3

Los 26 modelos se comparan en el test temporal 202530 de 188 estudiantes.
SVR RBF tiene el mayor R² (0.471418), seguido de TabICLv2 (0.464774),
TabPFN 2.5 original (0.464223) y LinXGBoost (0.463278).
El ranking coincide con el de RMSE porque ambos dependen de SSE en el mismo test.

## Archivos vigentes

- `modelos_r2.csv`: 26 resultados test, deltas, referencia y familia de cada contraste.
  Los 22 históricos usan SVM lineal como referencia principal; los cuatro
  recientes usan XGBoost. `delta_R2` e IC95% de delta corresponden a `Referencia`.
  `delta_R2_vs_SVM` y `delta_R2_vs_XGBoost` son deltas descriptivos comunes a los 26.
  Los IC absolutos de R² de los cuatro recientes no están en los reportes agregados
  y quedan vacíos. Holm21/Holm55 no se extienden a modelos ajenos a esas familias.
- `validacion_cruzada_r2.csv`: 26 filas con R² medio, SD poblacional (ddof=0),
  OOF reunido y test. TabPFN fine-tuned conserva sus campos CV vacíos porque sus
  pesos finales vieron todo train y no ofrecen una nueva OOF independiente.
- `folds_r2.csv`: 125 evaluaciones externas de los 25 modelos con OOF independiente.
- `contrastes_r2_vs_xgboost.csv`: contrastes publicados frente a XGBoost en las
  fuentes consolidadas, con su familia e IC95% de delta. No contiene todos los pares posibles.

La media de R² por fold, el R² OOF reunido y el R² test son cantidades distintas.
Los modelos se seleccionaron por RMSE en train; no se reoptimizó por R² ni
se ajustaron modelos al consolidar estas tablas.

## Conclusión estadística

LinXGBoost tiene ΔR²=+0.008637 frente a XGBoost, con Holm7=1.000.
Su R² OOF 0.427817 es inferior al de XGBoost original (0.465031).
El primer puesto de SVR RBF es descriptivo; frente a TabICLv2, ΔR²=+0.006644,
IC95% [-0.014880; 0.025163], Holm55=1.000.
Las variantes XGBoost no mejoran el resultado temporal del modelo original.

Holm55, Holm12 y Holm7 son familias distintas; no existe un ajuste único global
para los 26. RMSE y R² comparten contraste SSE y no son dos pruebas independientes.
El uso repetido del test hace exploratoria la inferencia. La falta de significancia
no demuestra equivalencia entre modelos.

[Ranking, métricas y conclusiones de los 26 modelos](../resumen_completo/resumen.md).
Las fuentes históricas se conservan en `historico_22/`.
Regeneración desde agregados: `python actualizar_comparaciones_e3.py`.
"""
    # El OOF de referencia se toma del reporte, sin redondeos escritos a mano.
    r2_note = r2_note.replace("0.465031", f"{float(cv['XGBoost']['R2_OOF_reunido']):.6f}")
    (output / "validacion_r2/resumen.md").write_text(r2_note, encoding="utf-8")
    print(json.dumps({"model_count": len(rows), "fold_evaluations": len(fold_rows), "consolidated_contrasts": len(contrast_rows), "training_performed": False}, ensure_ascii=False))
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=Path(__file__).resolve().parent)
    build(parser.parse_args().book.resolve())
