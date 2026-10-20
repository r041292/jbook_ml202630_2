"""LinXGBoost más fiel a de Vito (2017, arXiv:1710.03634).

Diferencias con `LinXGBoostRegressor` (se conserva intacto como versión histórica):
- Búsqueda exhaustiva de cortes en cada nodo (el artículo: «we exhaustively search at each node
  for the best axis-aligned split»); el histórico aproximaba con 12 cuantiles.
- Profundidad máxima muy grande: el artículo la fija alta y deja que `min_samples_leaf` y el mínimo
  para dividir limiten el árbol; el histórico buscaba max_depth en {2, 3, 4}.
Se mantienen los rasgos ya fieles: hojas Ridge con todas las variables, sesgo sin regularizar,
poda de ganancias negativas, hasta 5 árboles y variables centradas (StandardScaler).
"""
import numpy as np
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from entregable3 import make_pipeline
from evaluar_linxgboost_e3 import LinXGBoostRegressor, SEED


class LinXGBoostPaperRegressor(LinXGBoostRegressor):
    def __init__(self, n_estimators=2, learning_rate=0.1, max_depth=30, min_samples_leaf=60,
                 reg_lambda=10.0, gamma=0.0, random_state=SEED):
        super().__init__(n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth,
                         min_samples_leaf=min_samples_leaf, reg_lambda=reg_lambda, gamma=gamma,
                         max_bins=None, n_linear_features=None, random_state=random_state)

    def _candidate_positions(self, sorted_values):
        n = len(sorted_values)
        boundaries = np.flatnonzero(sorted_values[:-1] < sorted_values[1:]) + 1
        return boundaries[(boundaries >= self.min_samples_leaf) & (boundaries <= n - self.min_samples_leaf)]

    def _solve_pair(self, gram_left, cross_left, gram_right, cross_right):
        penalty = (0.5 * self.reg_lambda) * self._penalty_
        try:
            left = np.linalg.solve(gram_left + penalty, cross_left[..., None])[..., 0]
            right = np.linalg.solve(gram_right + penalty, cross_right[..., None])[..., 0]
        except np.linalg.LinAlgError:
            left = np.stack([np.linalg.lstsq(g + penalty, c, rcond=None)[0] for g, c in zip(gram_left, cross_left)])
            right = np.stack([np.linalg.lstsq(g + penalty, c, rcond=None)[0] for g, c in zip(gram_right, cross_right)])
        return left, right

    def _best_split(self, X, Z, residual, indices, parent_score):
        node_X, node_Z, node_residual = X[indices], Z[indices], residual[indices]
        n = len(indices)
        best = None
        total_gram = node_Z.T @ node_Z
        total_cross = node_Z.T @ node_residual
        for feature in range(X.shape[1]):
            column = node_X[:, feature]
            low, high = column.min(), column.max()
            if low == high:
                continue
            values = np.unique(column)
            if len(values) == 2:
                # Variable binaria: único corte posible; Gram directa sin acumulados sobre todo el nodo.
                left_mask = column <= low
                n_left = int(left_mask.sum())
                if min(n_left, n - n_left) < self.min_samples_leaf:
                    continue
                gram_left = (node_Z[left_mask].T @ node_Z[left_mask])[None]
                cross_left = (node_Z[left_mask].T @ node_residual[left_mask])[None]
                gram_right, cross_right = total_gram[None] - gram_left, total_cross[None] - cross_left
                boundaries, sorted_values = np.array([n_left]), None
                threshold_low, threshold_high = low, high
            else:
                order = np.argsort(column, kind="mergesort")
                sorted_values = column[order]
                boundaries = self._candidate_positions(sorted_values)
                if not len(boundaries):
                    continue
                sorted_Z, sorted_residual = node_Z[order], node_residual[order]
                prefix_gram = np.einsum("ni,nj->nij", sorted_Z, sorted_Z, optimize=True).cumsum(axis=0)
                prefix_cross = np.cumsum(sorted_Z * sorted_residual[:, None], axis=0)
                gram_left, cross_left = prefix_gram[boundaries - 1], prefix_cross[boundaries - 1]
                gram_right, cross_right = prefix_gram[-1] - gram_left, prefix_cross[-1] - cross_left
            coef_left, coef_right = self._solve_pair(gram_left, cross_left, gram_right, cross_right)
            score_left = np.einsum("ij,ij->i", cross_left, coef_left)
            score_right = np.einsum("ij,ij->i", cross_right, coef_right)
            gains = score_left + score_right - parent_score - self.gamma
            choice = int(np.argmax(gains))
            gain = float(gains[choice])
            if best is None or gain > best["gain"]:
                if sorted_values is None:
                    lo, hi = threshold_low, threshold_high
                else:
                    boundary = int(boundaries[choice])
                    lo, hi = float(sorted_values[boundary - 1]), float(sorted_values[boundary])
                best = {"feature": feature, "threshold": lo + (hi - lo) / 2.0, "gain": gain}
        return best


# Dominio de la búsqueda. max_depth queda fijo y alto (30): lo limitan min_samples_leaf y el mínimo para dividir
# (2·min_samples_leaf), como en el artículo. n_estimators ≤ 5 según sus experimentos.
# GRID (48 candidatos) se usó en la primera búsqueda fiel (cinco estrategias); sus mejores ensayos quedaron en el borde de
# SPACE_V1 (min_samples_leaf≈214/220, gamma≈0.99/1, reg_lambda hasta 90/100), por lo que la búsqueda ampliada (solo
# Optuna/TPE, 40 ensayos) usa SPACE con rangos más amplios.
GRID = {'modelo__n_estimators': [2, 5], 'modelo__learning_rate': [.06, .16],
        'modelo__min_samples_leaf': [40, 80, 160], 'modelo__reg_lambda': [3., 30.], 'modelo__gamma': [0., .2]}
SPACE_V1 = {'modelo__n_estimators': ('int', 1, 5), 'modelo__learning_rate': ('log', .03, .25),
            'modelo__min_samples_leaf': ('int', 30, 220), 'modelo__reg_lambda': ('log', .1, 100.),
            'modelo__gamma': ('real', 0., 1.)}
SPACE = {'modelo__n_estimators': ('int', 1, 5), 'modelo__learning_rate': ('log', .02, .4),
         'modelo__min_samples_leaf': ('int', 30, 450), 'modelo__reg_lambda': ('log', .1, 1000.),
         'modelo__gamma': ('log', 1e-3, 50.)}


def make_model():
    preprocessing = clone(make_pipeline().named_steps["preprocesamiento"])
    return Pipeline([("preprocesamiento", preprocessing), ("escalado_hojas", StandardScaler()),
                     ("modelo", LinXGBoostPaperRegressor())])
