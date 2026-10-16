"""Implementación experimental de logicDT: conjunciones + árbol + recocido.

Basada en Lau, Schikowski y Schwender (2024), doi:10.1007/s10994-023-06488-6.
No reproduce todo el paquete R. La discretización por cuantiles y las hojas
Ridge multivariables son adaptaciones explícitas para los predictores de E3.
"""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted


class LogicDTRegressor(RegressorMixin, BaseEstimator):
    """Busca conjuntos de términos AND (con negación) mediante simulated annealing.

    Los primeros n_numeric atributos son continuos; el resto deben ser binarios.
    Todos los cortes y decisiones se aprenden exclusivamente dentro de fit.
    """
    def __init__(self, n_numeric=8, quantiles=(.25, .5, .75), max_terms=5,
                 max_literals=2, max_depth=2, min_samples_leaf=40,
                 leaf_model='mean', ridge_alpha=10., n_iter=120,
                 n_restarts=2, random_state=42):
        self.n_numeric = n_numeric
        self.quantiles = quantiles
        self.max_terms = max_terms
        self.max_literals = max_literals
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.leaf_model = leaf_model
        self.ridge_alpha = ridge_alpha
        self.n_iter = n_iter
        self.n_restarts = n_restarts
        self.random_state = random_state

    def _bits(self, X):
        return np.column_stack([X[:, j] > cut for j, cut in self.bit_definitions_])

    @staticmethod
    def _terms_matrix(bits, terms):
        return np.column_stack([
            np.logical_and.reduce([~bits[:, j] if neg else bits[:, j]
                                   for j, neg in term]) for term in terms])

    def fit(self, X, y):
        X, y = check_X_y(X, y, dtype=float)
        if self.leaf_model not in ('mean', 'ridge'):
            raise ValueError('leaf_model debe ser mean o ridge')
        if not 0 <= self.n_numeric <= X.shape[1]:
            raise ValueError('n_numeric incompatible con X')
        if min(self.n_iter, self.n_restarts, self.max_terms, self.max_literals,
               self.max_depth, self.min_samples_leaf) < 1:
            raise ValueError('Los límites de búsqueda deben ser positivos')
        if self.ridge_alpha <= 0:
            raise ValueError('ridge_alpha debe ser positivo')
        if not np.isin(X[:, self.n_numeric:], [0, 1]).all():
            raise ValueError('Las columnas posteriores a n_numeric deben ser binarias')
        self.n_features_in_ = X.shape[1]
        self.bit_definitions_ = []
        for j in range(self.n_numeric):
            self.bit_definitions_.extend((j, float(q)) for q in
                np.unique(np.quantile(X[:, j], self.quantiles)))
        self.bit_definitions_.extend((j, .5) for j in range(self.n_numeric, X.shape[1]))
        bits = self._bits(X)
        # Retener únicamente cortes con soporte suficiente, aprendido en fit.
        valid = [j for j in range(bits.shape[1]) if
                 self.min_samples_leaf <= bits[:, j].sum() <= len(y)-self.min_samples_leaf]
        self.bit_definitions_ = [self.bit_definitions_[j] for j in valid]
        bits = bits[:, valid]
        Z = np.column_stack([np.ones(len(X)), X[:, :self.n_numeric]])
        cache = {}

        def leaf(ix):
            key = np.packbits(ix).tobytes()
            if key not in cache:
                target, design = y[ix], Z[ix]
                coef = np.zeros(Z.shape[1])
                if self.leaf_model == 'mean':
                    coef[0] = target.mean()
                else:
                    penalty = np.eye(Z.shape[1]) * self.ridge_alpha
                    penalty[0, 0] = 0
                    coef = np.linalg.solve(design.T @ design + penalty, design.T @ target)
                error = float(np.square(target - design @ coef).sum())
                if len(cache) > 5000:
                    cache.clear()
                cache[key] = (error, coef)
            return cache[key]

        def evaluate(terms):
            B = self._terms_matrix(bits, terms) if terms else np.empty((len(y), 0), bool)

            def grow(ix, depth):
                error, coef = leaf(ix)
                node = {'coef': coef, 'n': int(ix.sum())}
                best = None
                if depth < self.max_depth:
                    for k in range(B.shape[1]):
                        yes, no = ix & B[:, k], ix & ~B[:, k]
                        if min(yes.sum(), no.sum()) < self.min_samples_leaf:
                            continue
                        loss = leaf(yes)[0] + leaf(no)[0]
                        if loss < error - 1e-10 and (best is None or loss < best[0]):
                            best = loss, k, no, yes
                if best is None:
                    return error, node
                _, k, no, yes = best
                a, left = grow(no, depth+1)
                b, right = grow(yes, depth+1)
                node.update(term=k, left=left, right=right)
                return a+b, node

            error, tree = grow(np.ones(len(y), dtype=bool), 0)
            return error / len(y), tree

        rng = np.random.default_rng(self.random_state)
        global_score, global_tree = evaluate(())
        global_terms = ()
        self.search_history_ = []
        if bits.shape[1]:
            def random_term():
                size = int(rng.integers(1, min(self.max_literals, bits.shape[1])+1))
                js = rng.choice(bits.shape[1], size=size, replace=False)
                return tuple(sorted((int(j), bool(rng.integers(2))) for j in js))

            for restart in range(self.n_restarts):
                # Random singleton seeds plus a numerical predictor with large marginal gain.
                singles = [((j, False),) for j in range(bits.shape[1])]
                if restart == 0:
                    terms = (min(singles, key=lambda term: evaluate((term,))[0]),)
                else:
                    terms = tuple(sorted(set(random_term() for _ in range(self.max_terms))))
                score, tree = evaluate(terms)
                if score < global_score:
                    global_score, global_tree, global_terms = score, tree, terms
                for step in range(self.n_iter):
                    candidate = list(terms)
                    action = int(rng.integers(3))
                    if not candidate or (action == 0 and len(candidate) < self.max_terms):
                        candidate.append(random_term())
                    elif action == 1 and len(candidate) > 1:
                        candidate.pop(int(rng.integers(len(candidate))))
                    else:
                        k = int(rng.integers(len(candidate)))
                        # A local literal edit or a completely new conjunction.
                        term = list(candidate[k])
                        if rng.random() < .5:
                            pos = int(rng.integers(len(term)))
                            j, neg = term[pos]
                            term[pos] = (j, not neg)
                            candidate[k] = tuple(sorted(term))
                        else:
                            candidate[k] = random_term()
                    candidate = tuple(sorted(set(candidate)))
                    new_score, new_tree = evaluate(candidate)
                    temperature = max(float(np.var(y))*.05, 1e-8) * (.01 ** (step/max(1, self.n_iter-1)))
                    accepted = new_score <= score or rng.random() < np.exp(min(0., (score-new_score)/temperature))
                    if accepted:
                        terms, score, tree = candidate, new_score, new_tree
                    if new_score < global_score:
                        global_score, global_tree, global_terms = new_score, new_tree, candidate
                    self.search_history_.append({'restart': restart, 'step': step,
                        'proposal_mse': new_score, 'best_mse': global_score, 'accepted': bool(accepted)})
        self.terms_, self.tree_, self.training_mse_ = global_terms, global_tree, global_score
        return self

    def predict(self, X):
        check_is_fitted(self, 'tree_')
        X = check_array(X, dtype=float)
        if X.shape[1] != self.n_features_in_:
            raise ValueError('Número de columnas diferente al ajuste')
        B = self._terms_matrix(self._bits(X), self.terms_) if self.terms_ else np.empty((len(X), 0), bool)
        Z = np.column_stack([np.ones(len(X)), X[:, :self.n_numeric]])
        prediction = np.empty(len(X))

        def visit(node, ix):
            if 'term' not in node:
                prediction[ix] = Z[ix] @ node['coef']
                return
            mask = B[:, node['term']]
            visit(node['left'], ix & ~mask)
            visit(node['right'], ix & mask)
        visit(self.tree_, np.ones(len(X), bool))
        return prediction

    def describe_terms(self, feature_names):
        check_is_fitted(self, 'terms_')
        rows = []
        for k, term in enumerate(self.terms_):
            parts = []
            for bit, neg in term:
                j, cutoff = self.bit_definitions_[bit]
                parts.append(f'{feature_names[j]} {"<=" if neg else ">"} {cutoff:.5g}')
            rows.append({'termino': k, 'regla_en_escala_transformada': ' AND '.join(parts)})
        return rows
