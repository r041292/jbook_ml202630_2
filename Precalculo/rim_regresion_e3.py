"""Port experimental RIM para E3; PyTorch e índice BM25 local.

Referencia conceptual: Qin et al., KDD2021, arxiv:2108.05252.
Código consultado: qinjr/RIM@a6b4cdb347f306f9cf54a98fc994bf7112b53e9e.
Implementación propia: no requiere TensorFlow1 ni Elasticsearch.
"""
import random

import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.utils.validation import check_is_fitted

from entregable3 import FEATURES, CATEGORICAL, NUMERIC, make_pipeline


class FieldTokenizer:
    """15 campos; preparación canónica y discretización numérica interna."""
    def __init__(self, n_bins=8):
        self.n_bins = n_bins

    def fit(self, frame):
        self.preprocessor_ = clone(make_pipeline().named_steps['preprocesamiento']).fit(frame[FEATURES])
        transformed = self.preprocessor_.transform(frame[FEATURES])
        self.numeric_cuts_ = [np.unique(np.quantile(transformed[:, j], np.linspace(0, 1, self.n_bins+1)[1:-1]))
                              for j in range(len(NUMERIC))]
        ohe = self.preprocessor_.named_transformers_['cat'].named_steps['onehot']
        self.categories_ = [{value: k+1 for k, value in enumerate(values)} for values in ohe.categories_]
        self.sizes_ = [len(cuts)+2 for cuts in self.numeric_cuts_] + [len(c)+1 for c in self.categories_]
        # Cero es padding; cada campo reserva su propio token desconocido.
        self.offsets_ = np.r_[1, 1+np.cumsum(self.sizes_)[:-1]]
        self.vocab_size_ = int(1+sum(self.sizes_))
        return self

    def transform(self, frame):
        num = np.asarray(self.preprocessor_.transformers_[0][1].transform(
            frame[self.preprocessor_.transformers_[0][2]]))
        plain = np.asarray(self.preprocessor_.transformers_[1][1].transform(
            frame[self.preprocessor_.transformers_[1][2]]))
        numeric = np.column_stack([num, plain])
        cats = self.preprocessor_.named_transformers_['cat'].named_steps['imputer'].transform(frame[CATEGORICAL])
        codes = [np.searchsorted(cuts, numeric[:, j], side='right')+1 for j, cuts in enumerate(self.numeric_cuts_)]
        codes += [np.array([mapping.get(v, 0) for v in cats[:, j]]) for j, mapping in enumerate(self.categories_)]
        return np.asarray(np.column_stack(codes)+self.offsets_, dtype=np.int64)


class BM25Index:
    """BM25 de Lucene: TF=1 y longitud fija15 => suma de IDF de coincidencias."""
    def fit(self, tokens, groups):
        self.tokens_ = np.asarray(tokens)
        self.groups_ = np.asarray(groups)
        self.postings_ = {int(t): np.flatnonzero((tokens == t).any(axis=1)) for t in np.unique(tokens)}
        n = len(tokens)
        self.idf_ = {t: float(np.log1p((n-len(rows)+.5)/(len(rows)+.5))) for t, rows in self.postings_.items()}
        return self

    def retrieve(self, queries, k, query_groups=None):
        positions = np.full((len(queries), k), -1, dtype=int)
        for j, query in enumerate(queries):
            scores = np.zeros(len(self.tokens_), dtype=float)
            for token in query:
                if int(token) in self.postings_:
                    scores[self.postings_[int(token)]] += self.idf_[int(token)]
            if query_groups is not None:
                scores[self.groups_ == query_groups[j]] = 0
            valid = np.flatnonzero(scores > 0)
            # Desempate determinista por orden de fila; no usar objetivo para recuperar.
            order = np.lexsort((valid, -scores[valid]))[:k]
            positions[j, :len(order)] = valid[order]
        return positions


class RIMNetwork(nn.Module):
    """Atención bilineal, embeddings de etiquetas y todas las interacciones por pares."""
    def __init__(self, vocab_size, label_size, embedding_dim=8, hidden=(64, 32), dropout=.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.label_embedding = nn.Embedding(label_size, embedding_dim, padding_idx=0)
        fields = len(FEATURES)
        self.query_projection = nn.Linear(fields*embedding_dim, fields*embedding_dim, bias=False)
        self.register_buffer('pairs', torch.triu_indices(2*fields+1, 2*fields+1, offset=1))
        width = (2*fields+1)*embedding_dim+self.pairs.shape[1]
        self.mlp = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, hidden[0]), nn.ReLU(),
                                 nn.Dropout(dropout), nn.Linear(hidden[0], hidden[1]), nn.ReLU(), nn.Dropout(dropout))
        self.output = nn.Linear(hidden[1]+embedding_dim, 1)
        nn.init.normal_(self.embedding.weight, std=.05)
        nn.init.normal_(self.label_embedding.weight, std=.05)
        with torch.no_grad():
            self.embedding.weight[0].zero_()
            self.label_embedding.weight[0].zero_()

    def forward(self, target, neighbors, neighbor_labels, mask):
        query = self.embedding(target)
        keys = self.embedding(neighbors)
        projected = self.query_projection(query.flatten(1))
        logits = (keys.flatten(2)*projected[:, None]).sum(dim=-1)
        weights = torch.softmax(logits.masked_fill(~mask, -1e9), dim=1)*mask
        weights = weights/weights.sum(dim=1, keepdim=True).clamp_min(1e-12)
        retrieved = (weights[:, :, None, None]*keys).sum(dim=1)
        labels = (weights[:, :, None]*self.label_embedding(neighbor_labels)).sum(dim=1)
        fields = torch.cat([query, retrieved, labels[:, None]], dim=1)
        interactions = (fields[:, self.pairs[0]]*fields[:, self.pairs[1]]).sum(dim=-1)
        features = torch.cat([fields.flatten(1), interactions], dim=1)
        return self.output(torch.cat([self.mlp(features), labels], dim=1)).squeeze(1)


class RIMRegressor(RegressorMixin, BaseEstimator):
    """fit recibe groups separados; nunca se introducen ID/periodo como predictor."""
    def __init__(self, n_neighbors=10, embedding_dim=8, epochs=40, learning_rate=.001,
                 weight_decay=.001, n_bins=8, label_bins=10, batch_size=256,
                 dropout=.1, random_state=42):
        self.n_neighbors = n_neighbors
        self.embedding_dim = embedding_dim
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.n_bins = n_bins
        self.label_bins = label_bins
        self.batch_size = batch_size
        self.dropout = dropout
        self.random_state = random_state

    def _inputs(self, tokens, retrieved):
        valid = retrieved >= 0
        safe = np.maximum(retrieved, 0)
        neighbors = self.pool_tokens_[safe].copy()
        labels = self.pool_label_tokens_[safe].copy()
        neighbors[~valid] = 0
        labels[~valid] = 0
        return (torch.as_tensor(tokens, dtype=torch.long), torch.as_tensor(neighbors, dtype=torch.long),
                torch.as_tensor(labels, dtype=torch.long), torch.as_tensor(valid))

    def fit(self, X, y, groups=None):
        if groups is None:
            raise ValueError('RIM requiere groups explícitos para evitar recuperar el mismo estudiante.')
        if len(X) != len(y) or len(X) != len(groups) or pd.Series(groups).isna().any():
            raise ValueError('X/y/groups incompatibles o ID faltante.')
        if min(self.n_neighbors, self.embedding_dim, self.epochs, self.n_bins, self.label_bins, self.batch_size) < 1:
            raise ValueError('Los límites de entrenamiento deben ser positivos.')
        random.seed(self.random_state)
        np.random.seed(self.random_state)
        torch.manual_seed(self.random_state)
        torch.set_num_threads(1)
        self.tokenizer_ = FieldTokenizer(self.n_bins).fit(X)
        self.pool_tokens_ = self.tokenizer_.transform(X)
        self.pool_groups_ = np.asarray(groups).copy()
        self.index_ = BM25Index().fit(self.pool_tokens_, self.pool_groups_)
        y = np.asarray(y, dtype=float)
        if not np.isfinite(y).all():
            raise ValueError('Objetivo no finito.')
        self.label_cuts_ = np.unique(np.quantile(y, np.linspace(0, 1, self.label_bins+1)[1:-1]))
        self.pool_label_tokens_ = np.searchsorted(self.label_cuts_, y, side='right')+1
        self.y_mean_, self.y_scale_ = float(y.mean()), max(float(y.std()), 1e-8)
        self.network_ = RIMNetwork(self.tokenizer_.vocab_size_, len(self.label_cuts_)+2,
                                    self.embedding_dim, dropout=self.dropout)
        optimizer = torch.optim.Adam(self.network_.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        retrieval = self.index_.retrieve(self.pool_tokens_, self.n_neighbors, self.pool_groups_)
        self.training_retrieval_ = retrieval
        inputs = self._inputs(self.pool_tokens_, retrieval)
        target = torch.as_tensor((y-self.y_mean_)/self.y_scale_, dtype=torch.float32)
        rng = np.random.default_rng(self.random_state)
        self.loss_history_ = []
        for _ in range(self.epochs):
            self.network_.train()
            losses = []
            order = rng.permutation(len(y))
            for start in range(0, len(y), self.batch_size):
                ix = order[start:start+self.batch_size]
                optimizer.zero_grad(set_to_none=True)
                pred = self.network_(*(tensor[ix] for tensor in inputs))
                loss = (pred-target[ix]).square().mean()
                if not torch.isfinite(loss):
                    raise FloatingPointError('Loss RIM no finita.')
                loss.backward()
                nn.utils.clip_grad_norm_(self.network_.parameters(), 5., error_if_nonfinite=True)
                optimizer.step()
                losses.append(float(loss.detach()))
            self.loss_history_.append(float(np.mean(losses)))
        self.network_.eval()
        self.n_features_in_ = len(FEATURES)
        return self

    def predict(self, X, query_groups=None):
        check_is_fitted(self, 'network_')
        tokens = self.tokenizer_.transform(X)
        retrieval = self.index_.retrieve(tokens, self.n_neighbors, query_groups)
        inputs = self._inputs(tokens, retrieval)
        self.network_.eval()
        predictions = []
        with torch.no_grad():
            for start in range(0, len(X), self.batch_size):
                predictions.append(self.network_(*(v[start:start+self.batch_size] for v in inputs)).numpy())
        return np.concatenate(predictions).astype(float)*self.y_scale_+self.y_mean_
