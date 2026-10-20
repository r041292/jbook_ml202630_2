"""logicDT fiel al artículo (Lau, Schikowski y Schwender, Machine Learning 113:933-992, 2024).

Diferencias con `logicdt_propio.py` (adaptación histórica, que se conserva intacta):
- Predictores binarios = indicadores one-hot (columnas posteriores a `n_numeric`); las
  covariables cuantitativas (primeras `n_numeric`) NO se binarizan: entran en modelos de
  regresión lineal en las hojas (Sec. 3.5.1) y en el criterio de división (Sec. 3.5.2).
- Estados = conjuntos de términos (conjunciones con negación) con `max_vars` variables en
  total y `max_conj` términos; vecinos de la Fig. 3 (intercambiar/negar una variable,
  añadir/quitar una variable de un término, añadir/quitar un término de una variable).
  El modelo individual no elimina conjunciones y parte de exactamente `max_conj` términos.
- Árbol: divisiones solo por términos; con covariables se elige la división de menor valor p
  de la razón de verosimilitud (modelos gaussianos anidados, α = 0.5); `nodesize` mínimo por
  hoja y `conjsize` mínimo por conjunción y su negación; sin poda ni profundidad máxima.
- Búsqueda: recocido simulado con enfriamiento adaptativo (Apéndice 1): temperatura inicial
  tal que el 90 % de los vecinos peores se acepta (paseo aleatorio), cadenas de longitud fija,
  t' = t·exp(−λ·t/σ(t)) (Huang et al. 1986), enfriamiento anticipado con 50 % de aceptación
  y parada tras 5 cadenas consecutivas con tasa de aceptación ajustada < 1 %.
Desviaciones de presupuesto (documentadas): el artículo recomienda cientos de miles de
iteraciones; aquí `chain_length`, `n_random_walk` y `max_iterations` acotan el coste.
"""
import numpy as np
from scipy.stats import chi2
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted

ALPHA_SPLIT = 0.5          # umbral de significación liberal del artículo (Sec. 3.5.2)
RIDGE = 1e-8               # estabilidad numérica de las ecuaciones normales


class LogicDTFaithfulRegressor(RegressorMixin, BaseEstimator):
    def __init__(self, n_numeric=8, max_conj=2, extra_vars=0, nodesize_frac=.05,
                 cooling_lambda=.1, chain_length=200, n_random_walk=300,
                 accept_start=.9, max_iterations=10000, stop_chains=5, random_state=42):
        self.n_numeric = n_numeric
        self.max_conj = max_conj
        self.extra_vars = extra_vars
        self.nodesize_frac = nodesize_frac
        self.cooling_lambda = cooling_lambda
        self.chain_length = chain_length
        self.n_random_walk = n_random_walk
        self.accept_start = accept_start
        self.max_iterations = max_iterations
        self.stop_chains = stop_chains
        self.random_state = random_state

    # ---- utilidades de términos -------------------------------------------------------
    @staticmethod
    def _term_mask(B, term):
        mask = np.ones(len(B), dtype=bool)
        for var, negated in term:
            mask &= ~B[:, var] if negated else B[:, var]
        return mask

    def _valid_term(self, B, term, cache):
        key = term
        if key not in cache:
            support = int(self._term_mask(B, term).sum())
            cache[key] = self.conjsize_ <= support <= len(B) - self.conjsize_
        return cache[key]

    # ---- ajuste de hojas y árbol -------------------------------------------------------
    def _leaf(self, ix_bool):
        key = np.packbits(ix_bool).tobytes()
        hit = self._leaf_cache.get(key)
        if hit is None:
            Z, y = self._Z[ix_bool], self._y[ix_bool]
            coef = np.linalg.solve(Z.T @ Z + RIDGE * np.eye(Z.shape[1]), Z.T @ y)
            rss = float(np.square(y - Z @ coef).sum())
            if len(self._leaf_cache) > 20000:
                self._leaf_cache.clear()
            hit = self._leaf_cache[key] = (rss, coef)
        return hit

    def _grow(self, T, ix, used):
        rss, coef = self._leaf(ix)
        node = {'coef': coef}
        n = int(ix.sum())
        best = None
        for k in range(T.shape[1]):
            if k in used:
                continue
            yes, no = ix & T[:, k], ix & ~T[:, k]
            ny = int(yes.sum())
            if ny < self.nodesize_ or n - ny < self.nodesize_:
                continue
            full = self._leaf(yes)[0] + self._leaf(no)[0]
            if self._has_covariates:
                # Estadístico de razón de verosimilitud gaussiana: n·log(RSS_reducido/RSS_completo).
                stat = n * np.log(max(rss, 1e-300) / max(full, 1e-300))
                better = stat > self._lrt_threshold
            else:
                stat = (rss - full) / n   # reducción de impureza MSE (hojas de media)
                better = stat > 1e-12
            if better and (best is None or stat > best[0]):
                best = (stat, k, yes, no)
        if best is None:
            return rss, node
        _, k, yes, no = best
        a, left = self._grow(T, no, used | {k})
        b, right = self._grow(T, yes, used | {k})
        node.update(term=k, left=left, right=right)
        return a + b, node

    def _evaluate(self, B, terms):
        if not terms:
            rss, node = self._grow(np.empty((len(self._y), 0), bool), np.ones(len(self._y), bool), frozenset())
            return rss / len(self._y), node
        T = np.column_stack([self._term_mask(B, t) for t in terms])
        rss, node = self._grow(T, np.ones(len(self._y), bool), frozenset())
        return rss / len(self._y), node

    # ---- vecindad (Fig. 3) -------------------------------------------------------------
    def _neighbors(self, terms, n_vars):
        """Lista de movimientos válidos por categoría; el muestreo es uniforme sobre todos."""
        moves = []
        total_vars = sum(len(t) for t in terms)
        for ti, term in enumerate(terms):
            present = {v for v, _ in term}
            for pi, (v, neg) in enumerate(term):
                moves.append(('negate', ti, pi, None))
                moves.extend(('exchange', ti, pi, w) for w in range(n_vars) if w not in present)
                if len(term) > 1:
                    moves.append(('drop_var', ti, pi, None))
            if total_vars < self.max_vars_:
                moves.extend(('add_var', ti, None, (w, neg2)) for w in range(n_vars) if w not in present
                             for neg2 in (False, True))
        if len(terms) < self.max_conj and total_vars < self.max_vars_:
            moves.extend(('add_term', None, None, (w, neg2)) for w in range(n_vars) for neg2 in (False, True))
        return moves

    def _apply(self, terms, move):
        kind, ti, pi, arg = move
        terms = [list(t) for t in terms]
        if kind == 'negate':
            v, neg = terms[ti][pi]
            terms[ti][pi] = (v, not neg)
        elif kind == 'exchange':
            _, neg = terms[ti][pi]
            terms[ti][pi] = (arg, neg)
        elif kind == 'drop_var':
            terms[ti].pop(pi)
        elif kind == 'add_var':
            terms[ti].append(arg)
        elif kind == 'add_term':
            terms.append([arg])
        out = tuple(tuple(sorted(t)) for t in terms)
        if len(set(out)) != len(out):
            return None
        return out

    def _propose(self, terms, n_vars, rng, B, support_cache):
        moves = self._neighbors(terms, n_vars)
        for _ in range(50):
            if not moves:
                return None
            candidate = self._apply(terms, moves[int(rng.integers(len(moves)))])
            if candidate is not None and all(self._valid_term(B, t, support_cache) for t in candidate):
                return tuple(sorted(candidate))
        return None

    # ---- ajuste ------------------------------------------------------------------------
    def fit(self, X, y):
        X, y = check_X_y(X, y, dtype=float)
        n_numeric = self.n_numeric
        if not 0 <= n_numeric <= X.shape[1] or self.max_conj < 1 or self.extra_vars < 0:
            raise ValueError('Parámetros incompatibles con X.')
        binary = X[:, n_numeric:]
        if not np.isin(binary, [0, 1]).all():
            raise ValueError('Las columnas posteriores a n_numeric deben ser binarias.')
        B = binary.astype(bool)
        n, n_vars = B.shape
        self.n_features_in_ = X.shape[1]
        self.max_vars_ = self.max_conj + min(int(self.extra_vars), int(self.max_conj))
        self.nodesize_ = self.conjsize_ = max(5, int(np.floor(self.nodesize_frac * n)))
        self._has_covariates = n_numeric > 0
        self._lrt_threshold = float(chi2.isf(ALPHA_SPLIT, df=n_numeric + 1)) if self._has_covariates else 0.
        self._Z = np.column_stack([np.ones(n), X[:, :n_numeric]])
        self._y = y.astype(float)
        self._leaf_cache = {}
        rng = np.random.default_rng(self.random_state)
        support_cache = {}

        singles = [((v, False),) for v in range(n_vars) if self._valid_term(B, ((v, False),), support_cache)]
        # Estado inicial: mejor variable única y relleno voraz hasta max_conj términos (sin eliminación de términos).
        scored = sorted(((self._evaluate(B, (t,))[0], t) for t in singles), key=lambda s: s[0])
        self.search_history_ = []
        if not scored:
            self.terms_ = ()
            self.training_mse_, self.tree_ = self._evaluate(B, ())
            self.n_iterations_ = 0
            return self
        state = (scored[0][1],)
        while len(state) < min(self.max_conj, len(scored)):
            options = [t for _, t in scored if t not in state][:15]
            state = min((tuple(sorted(state + (t,))) for t in options),
                        key=lambda s: self._evaluate(B, s)[0])
        score, tree = self._evaluate(B, state)
        best_state, best_score, best_tree = state, score, tree

        # Paseo aleatorio para la temperatura inicial: aceptar todos los vecinos válidos.
        worse, walk_state, walk_score = [], state, score
        for _ in range(self.n_random_walk):
            nxt = self._propose(walk_state, n_vars, rng, B, support_cache)
            if nxt is None:
                continue
            nxt_score, nxt_tree = self._evaluate(B, nxt)
            if nxt_score > walk_score:
                worse.append(nxt_score - walk_score)
            if nxt_score < best_score:
                best_state, best_score, best_tree = nxt, nxt_score, nxt_tree
            walk_state, walk_score = nxt, nxt_score
        if worse:
            deltas = np.asarray(worse)
            lo, hi = 1e-12, float(deltas.max()) * 1e3 + 1e-12
            for _ in range(60):   # bisección: media de exp(-Δ/t) = aceptación objetivo
                mid = np.sqrt(lo * hi)
                if np.exp(-deltas / mid).mean() < self.accept_start:
                    lo = mid
                else:
                    hi = mid
            temperature = float(np.sqrt(lo * hi))
        else:
            temperature = max(float(np.var(y)) * .05, 1e-8)

        iterations, quiet = 0, 0
        while iterations < self.max_iterations and quiet < self.stop_chains:
            scores_chain, accepted, changed = [], 0, 0
            for _ in range(self.chain_length):
                nxt = self._propose(state, n_vars, rng, B, support_cache)
                iterations += 1
                if nxt is None:
                    scores_chain.append(score)
                    continue
                nxt_score, nxt_tree = self._evaluate(B, nxt)
                if nxt_score <= score or rng.random() < np.exp((score - nxt_score) / temperature):
                    accepted += 1
                    changed += int(abs(nxt_score - score) > 1e-12)
                    state, score, tree = nxt, nxt_score, nxt_tree
                if score < best_score:
                    best_state, best_score, best_tree = state, score, tree
                scores_chain.append(score)
                if accepted >= .5 * self.chain_length:      # enfriamiento anticipado (Apéndice 1)
                    break
                if iterations >= self.max_iterations:
                    break
            sigma = float(np.std(scores_chain))
            quiet = quiet + 1 if changed / max(len(scores_chain), 1) < .01 else 0
            self.search_history_.append({'temperature': temperature, 'sigma': sigma, 'accepted': accepted,
                                         'changed': changed, 'best_mse': best_score})
            if sigma <= 1e-14:
                break
            temperature *= float(np.exp(-self.cooling_lambda * temperature / sigma))
        self.n_iterations_ = iterations
        self.terms_, self.training_mse_, self.tree_ = best_state, best_score, best_tree
        self._leaf_cache = {}
        return self

    def predict(self, X):
        check_is_fitted(self, 'tree_')
        X = check_array(X, dtype=float)
        if X.shape[1] != self.n_features_in_:
            raise ValueError('Número de columnas diferente al ajuste.')
        B = X[:, self.n_numeric:].astype(bool)
        Z = np.column_stack([np.ones(len(X)), X[:, :self.n_numeric]])
        T = np.column_stack([self._term_mask(B, t) for t in self.terms_]) if self.terms_ else np.empty((len(X), 0), bool)
        out = np.empty(len(X))

        def visit(node, ix):
            if 'term' not in node:
                out[ix] = Z[ix] @ node['coef']
                return
            mask = T[:, node['term']]
            visit(node['left'], ix & ~mask)
            visit(node['right'], ix & mask)
        visit(self.tree_, np.ones(len(X), bool))
        return out

    def describe_terms(self, feature_names):
        check_is_fitted(self, 'terms_')
        return [{'termino': k, 'regla': ' AND '.join(f'{"NOT " if neg else ""}{feature_names[self.n_numeric + v]}'
                                                       for v, neg in term)} for k, term in enumerate(self.terms_)]


# Dominio de la búsqueda (protocolo nuevo). max_vars = max_conj + min(extra_vars, max_conj) cumple
# max_conj ≤ max_vars ≤ 2·max_conj del artículo; nodesize = conjsize = ⌊frac·n⌋ con frac ∈ {1, 5, 10 %}.
GRID = [{'modelo__max_conj': [1], 'modelo__extra_vars': [0, 1], 'modelo__nodesize_frac': [.01, .05, .1]},
        {'modelo__max_conj': [2, 3, 4], 'modelo__extra_vars': [0, 1, 2], 'modelo__nodesize_frac': [.01, .05, .1]}]
SPACE = {'modelo__max_conj': ('int', 1, 4), 'modelo__extra_vars': ('int', 0, 2),
         'modelo__nodesize_frac': ('log', .01, .1)}


def make_model():
    """Preparación canónica E3 + logicDT fiel: columnas numéricas como covariables, one-hot como binarias."""
    from sklearn.base import clone
    from sklearn.pipeline import Pipeline
    from entregable3 import NUMERIC, make_pipeline
    return Pipeline([('preprocesamiento', clone(make_pipeline().named_steps['preprocesamiento'])),
                     ('modelo', LogicDTFaithfulRegressor(n_numeric=len(NUMERIC)))])
