"""Categorías nativas de XGBoost: vocabulario aprendido solo en fit."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


class NativeCategories(TransformerMixin, BaseEstimator):
    """Recibe el DataFrame imputado y convierte cat__* a dtype category.

    Categorías desconocidas se representan como faltantes, nunca se aprende
    vocabulario de validación/test. No genera columnas one-hot.
    """
    def fit(self, X, y=None):
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        self.n_features_in_ = len(self.feature_names_in_)
        self.categories_ = {c: sorted(X[c].dropna().unique().tolist())
                            for c in X.columns if c.startswith('cat__')}
        return self

    def transform(self, X):
        check_is_fitted(self, 'categories_')
        result = X.loc[:, self.feature_names_in_].copy()
        for column, categories in self.categories_.items():
            known = result[column].where(result[column].isin(categories), np.nan)
            result[column] = pd.Categorical(known, categories=categories)
        return result

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, 'feature_names_in_')
        return self.feature_names_in_.copy()
