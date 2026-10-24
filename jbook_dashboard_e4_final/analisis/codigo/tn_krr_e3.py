"""Truncated-Regularized Newton Kernel Ridge Regression for E3.

The dual coefficients are computed with the truncated linear-CG procedure
described by Maalouf and Homouz (2014), rather than a closed-form solver.
"""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted

from entregable3 import make_pipeline as make_e3_pipeline


class TruncatedNewtonKernelRidgeRegressor(RegressorMixin, BaseEstimator):
    """RBF KRR solved with the paper's truncated linear conjugate gradient.

    Parameters follow the papers' notation: ``alpha`` is lambda in
    ``(K + lambda I) a = y`` and ``gamma`` controls the RBF kernel.
    The solver defaults reproduce the published controls: 200 CG iterations,
    residual norm threshold 0.5, and termination after 25 non-improving steps.
    """

    def __init__(self, alpha=1.0, gamma=0.01, max_iter=200,
                 cg_tolerance=0.5, max_no_improve=25):
        self.alpha = alpha
        self.gamma = gamma
        self.max_iter = max_iter
        self.cg_tolerance = cg_tolerance
        self.max_no_improve = max_no_improve

    @staticmethod
    def _rbf_kernel(X, Y, gamma):
        x_norm = np.einsum('ij,ij->i', X, X)
        y_norm = np.einsum('ij,ij->i', Y, Y)
        squared_distances = x_norm[:, None] + y_norm[None, :] - 2.0 * (X @ Y.T)
        np.maximum(squared_distances, 0.0, out=squared_distances)
        return np.exp(-gamma * squared_distances)

    def fit(self, X, y):
        X, y = check_X_y(X, y, dtype=np.float64, y_numeric=True,
                         ensure_2d=True, multi_output=False)
        if not np.isfinite([self.alpha, self.gamma, self.cg_tolerance]).all():
            raise ValueError('alpha, gamma y cg_tolerance deben ser finitos.')
        if self.alpha <= 0:
            raise ValueError('alpha debe ser > 0 para que K + alpha*I sea definida positiva.')
        if self.gamma <= 0:
            raise ValueError('gamma debe ser > 0 para el kernel RBF.')
        if self.max_iter < 1 or self.max_no_improve < 1 or self.cg_tolerance < 0:
            raise ValueError('Los límites del solver deben ser positivos y la tolerancia no negativa.')

        self.X_fit_ = np.array(X, dtype=np.float64, copy=True)
        self.n_features_in_ = self.X_fit_.shape[1]
        kernel = self._rbf_kernel(self.X_fit_, self.X_fit_, float(self.gamma))
        system = kernel
        system.flat[::len(system) + 1] += float(self.alpha)

        # Algorithm 1 starts from an initial coefficient vector; use zero,
        # which makes its initial residual exactly y.
        coefficients = np.zeros_like(y, dtype=np.float64)
        residual = y.astype(np.float64, copy=True)
        direction = residual.copy()
        residual_sq = float(residual @ residual)
        residual_norm = float(np.sqrt(residual_sq))
        best_residual_norm = residual_norm
        no_improvement = 0
        converged = residual_norm <= self.cg_tolerance
        stop_reason = 'residual_tolerance' if converged else 'max_iterations'
        n_iter = 0

        for iteration in range(1, int(self.max_iter) + 1):
            if converged:
                break
            system_direction = system @ direction
            curvature = float(direction @ system_direction)
            if not np.isfinite(curvature) or curvature <= 0.0:
                raise FloatingPointError('El sistema KRR perdió curvatura positiva durante CG.')

            step = residual_sq / curvature
            coefficients += step * direction
            residual -= step * system_direction
            next_residual_sq = float(residual @ residual)
            residual_norm = float(np.sqrt(max(next_residual_sq, 0.0)))
            n_iter = iteration

            if residual_norm <= self.cg_tolerance:
                converged = True
                stop_reason = 'residual_tolerance'
                residual_sq = next_residual_sq
                break

            if residual_norm < best_residual_norm:
                best_residual_norm = residual_norm
                no_improvement = 0
            else:
                no_improvement += 1
                if no_improvement >= self.max_no_improve:
                    stop_reason = 'no_improvement'
                    residual_sq = next_residual_sq
                    break

            if next_residual_sq == 0.0:
                converged = True
                stop_reason = 'zero_residual'
                residual_sq = next_residual_sq
                break

            conjugacy = next_residual_sq / residual_sq
            direction = residual + conjugacy * direction
            residual_sq = next_residual_sq

        self.dual_coef_ = coefficients
        self.n_iter_ = n_iter
        self.residual_norm_ = residual_norm
        self.converged_ = converged
        self.stop_reason_ = stop_reason
        return self

    def predict(self, X):
        check_is_fitted(self, ['X_fit_', 'dual_coef_'])
        X = check_array(X, dtype=np.float64, ensure_2d=True)
        if X.shape[1] != self.n_features_in_:
            raise ValueError(f'X debe tener {self.n_features_in_} columnas.')
        kernel = self._rbf_kernel(X, self.X_fit_, float(self.gamma))
        return kernel @ self.dual_coef_


def make_model(alpha=1.0, gamma=0.01):
    """Build the E3 preprocessing pipeline plus the paper's TR-KRR solver."""
    preprocessor = clone(make_e3_pipeline().named_steps['preprocesamiento'])
    estimator = TruncatedNewtonKernelRidgeRegressor(alpha=alpha, gamma=gamma)
    return Pipeline([('preprocesamiento', preprocessor), ('modelo', estimator)])
