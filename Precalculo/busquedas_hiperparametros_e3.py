"""Cinco estrategias: cada fitness aprende un pipeline nuevo por fold interno.

Sin test en esta API. Los presupuestos son fijos antes de ejecutar el experimento.
"""
import copy
import hashlib
import json
import math
import random
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import optuna
from deap import base, creator, tools
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import ParameterGrid
from threadpoolctl import threadpool_limits

from entregable3 import FEATURES, TARGET, GROUP, GRID as SVM_GRID, make_pipeline, grouped_splits, metrics
from modelos_clasicos import GRIDS, classic_pipeline
from evaluar_decision_tree_e3 import GRID as TREE_GRID, make_tree

METHODS = ['Grid Search', 'Random Search', 'Bayesiana TPE', 'Genética DEAP', 'Successive Halving']
GRIDS_ALL = {'svm': SVM_GRID, **GRIDS, 'decision_tree': TREE_GRID}
# tipo, dominio; los intervalos amplían los puntos discretos del grid histórico.
SPACES = {
    'svm': {'modelo__C': ('log', .01, 10.), 'modelo__epsilon': ('real', 0., 1.)},
    'knn': {'modelo__n_neighbors': ('int', 5, 101), 'modelo__weights': ('cat', ['uniform', 'distance']), 'modelo__p': ('cat', [1, 2])},
    'ridge': {'modelo__alpha': ('log', .01, 1000.)},
    'lasso': {'modelo__alpha': ('log', .0001, .1)},
    'forest': {'modelo__n_estimators': ('int', 150, 500), 'modelo__max_depth': ('cat', [4, 6, 8, 12, None]),
               'modelo__min_samples_leaf': ('int', 2, 20)},
    'xgboost': {'modelo__n_estimators': ('int', 150, 500), 'modelo__max_depth': ('int', 1, 6),
                'modelo__learning_rate': ('log', .01, .1)},
    'decision_tree': {'modelo__max_depth': ('cat', [2, 3, 4, 6, 8, None]),
                      'modelo__min_samples_leaf': ('int', 2, 30), 'modelo__ccp_alpha': ('real', 0., .01)},
}
BUDGET = {'random_trials': 16, 'bayes_trials': 20, 'startup_trials': 6, 'ei_candidates': 24,
          'population': 8, 'generations': 3, 'elites': 1, 'tournament': 3,
          'crossover_probability': .8, 'uniform_crossover_gene_probability': .5,
          'mutation_probability': .3, 'halving_candidates': 16, 'reduction_factor': 2,
          'fidelities': [.25, .5, 1.], 'n_jobs': 4, 'seed': 42}


def pipeline_for(key):
    return make_pipeline() if key == 'svm' else make_tree() if key == 'decision_tree' else classic_pipeline(key)


def fingerprint(parameters):
    return json.dumps(parameters, sort_keys=True, separators=(',', ':'))


def decode(genes, key):
    params = {}
    for gene, (name, spec) in zip(genes, SPACES[key].items()):
        u = min(max(float(gene), 0.), np.nextafter(1., 0.))
        if spec[0] == 'cat':
            params[name] = spec[1][min(int(u*len(spec[1])), len(spec[1])-1)]
        elif spec[0] == 'int':
            params[name] = min(spec[2], spec[1] + int(u*(spec[2]-spec[1]+1)))
        elif spec[0] == 'log':
            params[name] = float(math.exp(math.log(spec[1])+u*math.log(spec[2]/spec[1])))
        else:
            params[name] = float(spec[1]+u*(spec[2]-spec[1]))
    return params


def suggest(trial, key):
    params = {}
    for name, spec in SPACES[key].items():
        if spec[0] == 'cat': params[name] = trial.suggest_categorical(name, spec[1])
        elif spec[0] == 'int': params[name] = trial.suggest_int(name, spec[1], spec[2])
        else: params[name] = trial.suggest_float(name, spec[1], spec[2], log=spec[0] == 'log')
    return params


def manual_fold(key, parameters, frame, fit, val, fidelity, fold):
    """Factory NUEVA por evaluación/fold: ninguna transformación fuera de fit."""
    groups = frame.iloc[fit][GROUP].unique()
    order = np.random.default_rng(42+fold).permutation(groups)
    selected = order[:max(2, math.ceil(len(order)*fidelity))]
    actual = fit[frame.iloc[fit][GROUP].isin(selected).to_numpy()]
    fitting, validation = frame.iloc[actual], frame.iloc[val]
    assert not set(fitting[GROUP]) & set(validation[GROUP])
    model = pipeline_for(key).set_params(**parameters)
    info = {'fold': fold, 'fit_rows': len(actual), 'validation_rows': len(val),
            'fit_groups': fitting[GROUP].nunique(), 'validation_groups': validation[GROUP].nunique(),
            'shared_groups': 0, 'fidelity': fidelity, 'fit_seconds': None, 'predict_seconds': None,
            'fit_index_sha256': hashlib.sha256(np.asarray(actual, dtype='int64').tobytes()).hexdigest()}
    # KNN n_neighbors nunca se corrige silenciosamente: candidato inviable se registra.
    clock = time.perf_counter()
    try:
        with threadpool_limits(limits=1), warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories', category=UserWarning)
            warnings.simplefilter('error', ConvergenceWarning)
            model.fit(fitting[FEATURES], fitting[TARGET])
            info['fit_seconds'] = time.perf_counter()-clock
            clock = time.perf_counter()
            pred = model.predict(validation[FEATURES])
            info['predict_seconds'] = time.perf_counter()-clock
            info.update(status='completa', RMSE=metrics(validation[TARGET], pred)['RMSE'])
    except Exception as error:
        phase = 'fit_seconds' if info['fit_seconds'] is None else 'predict_seconds'
        info[phase] = time.perf_counter()-clock
        info.update(status='fallida', RMSE=None, error=f'{type(error).__name__}: {error}')
    return info


def diversity(population, key):
    """Diversidad fenotípica y entropía de genes (10 bins para continuos)."""
    parameters = [decode(ind, key) for ind in population]
    entropy = []
    for i, (_, spec) in enumerate(SPACES[key].items()):
        if spec[0] == 'cat':
            values = [fingerprint({str(i): list(p.values())[i]}) for p in parameters]
            bins = len(spec[1])
        elif spec[0] == 'int':
            values = [list(p.values())[i] for p in parameters]
            bins = min(len(population), spec[2]-spec[1]+1)
        else:
            values = [min(9, int(ind[i]*10)) for ind in population]
            bins = min(10, len(population))
        _, counts = np.unique(values, return_counts=True)
        probabilities = counts/counts.sum()
        entropy.append(float(-np.sum(probabilities*np.log(probabilities))/np.log(min(bins, len(population)))) if bins > 1 else 0.)
    return {'unique_fraction': len({fingerprint(p) for p in parameters})/len(population),
            'gene_entropy': float(np.mean(entropy))}


class Search:
    def __init__(self, key, frame, outer, timing, directory, budget=None):
        self.key, self.frame, self.outer = key, frame.reset_index(drop=True), outer
        self.splits = grouped_splits(self.frame)
        self.timing, self.directory = timing, Path(directory)
        self.budget = {**BUDGET, **(budget or {})}
        self.trials, self.evolution, self.summaries = [], [], []
        self.method, self.cache = '', {}
        self.trial_file = self.directory / f'trials_{key}_{outer}.jsonl'

    def evaluate(self, params, fidelity=1.):
        token = (fingerprint(params), fidelity)
        if token in self.cache:
            return self.cache[token]
        clock = time.perf_counter()
        scores = joblib.Parallel(n_jobs=self.budget['n_jobs'])(
            joblib.delayed(manual_fold)(self.key, params, self.frame, fit, val, fidelity, fold)
            for fold, (fit, val) in enumerate(self.splits, 1))
        valid = all(s['status'] == 'completa' for s in scores)
        values = [s['RMSE'] for s in scores] if valid else []
        trial = {'method': self.method, 'params': params, 'fidelity': fidelity,
                 'RMSE': float(np.mean(values)) if valid else None,
                 'sd_RMSE': float(np.std(values)) if valid else None,
                 'seconds': time.perf_counter()-clock, 'inner_folds': scores,
                 'status': 'completa' if valid else 'fallida', 'trial': len(self.trials)+1}
        self.trials.append(trial)
        with self.trial_file.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(trial, ensure_ascii=False, default=lambda x: x.item())+'\n')
        self.cache[token] = trial
        return trial

    def fitness(self, ind):
        result = self.evaluate(decode(ind, self.key))
        return (result['RMSE'] if result['RMSE'] is not None else float('inf'),)

    def genetic(self):
        config = self.budget
        random.seed(config['seed'])
        if not hasattr(creator, 'E3FitnessMin'):
            creator.create('E3FitnessMin', base.Fitness, weights=(-1.,))
            creator.create('E3Individual', list, fitness=creator.E3FitnessMin)
        toolbox = base.Toolbox()
        toolbox.register('individual', tools.initRepeat, creator.E3Individual, random.random, len(SPACES[self.key]))
        toolbox.register('population', tools.initRepeat, list, toolbox.individual)
        toolbox.register('select', tools.selTournament, tournsize=config['tournament'])
        toolbox.register('mate', tools.cxUniform, indpb=config['uniform_crossover_gene_probability'])
        def mutate(individual):
            for i in range(len(individual)):
                if random.random() < 1/len(individual): individual[i] = random.random()
            return (individual,)
        toolbox.register('mutate', mutate)
        population = toolbox.population(n=config['population'])
        for generation in range(config['generations']+1):
            for individual in population:
                if not individual.fitness.valid: individual.fitness.values = self.fitness(individual)
            row = {'generation': generation, 'best_RMSE': min(i.fitness.values[0] for i in population),
                   'mean_RMSE': float(np.mean([i.fitness.values[0] for i in population])),
                   **diversity(population, self.key)}
            self.evolution.append(row)
            if generation == config['generations']: break
            elites = list(map(copy.deepcopy, tools.selBest(population, config['elites'])))
            offspring = list(map(copy.deepcopy, toolbox.select(population, config['population']-config['elites'])))
            for a, b in zip(offspring[::2], offspring[1::2]):
                if random.random() < config['crossover_probability']:
                    toolbox.mate(a, b)
                    del a.fitness.values, b.fitness.values
            for individual in offspring:
                if random.random() < config['mutation_probability']:
                    toolbox.mutate(individual)
                    del individual.fitness.values
            population = elites + offspring

    def run_method(self, method):
        self.method, self.cache = method, {}
        before = len(self.trials)
        clock = time.perf_counter()
        label = f'{self.key} / {self.outer} / {method}'
        with self.timing.measure('Búsqueda', label, len(self.frame), model=self.key, method=method,
                                 outer=self.outer, refit=False, n_jobs=self.budget['n_jobs']):
            rng = np.random.default_rng(self.budget['seed'])
            if method == METHODS[0]:
                for params in ParameterGrid(GRIDS_ALL[self.key]): self.evaluate(params)
            elif method == METHODS[1]:
                for _ in range(self.budget['random_trials']): self.evaluate(decode(rng.random(len(SPACES[self.key])), self.key))
            elif method == METHODS[2]:
                optuna.logging.set_verbosity(optuna.logging.WARNING)
                sampler = optuna.samplers.TPESampler(seed=self.budget['seed'], multivariate=False,
                    n_startup_trials=self.budget['startup_trials'], n_ei_candidates=self.budget['ei_candidates'])
                study = optuna.create_study(direction='minimize', sampler=sampler)
                def objective(trial):
                    result = self.evaluate(suggest(trial, self.key))
                    return result['RMSE'] if result['RMSE'] is not None else float('inf')
                study.optimize(objective, n_trials=self.budget['bayes_trials'], n_jobs=1)
            elif method == METHODS[3]: self.genetic()
            else:
                candidates = [decode(rng.random(len(SPACES[self.key])), self.key) for _ in range(self.budget['halving_candidates'])]
                for fraction in self.budget['fidelities']:
                    results = [self.evaluate(params, fraction) for params in candidates]
                    results.sort(key=lambda t: t['RMSE'] if t['RMSE'] is not None else float('inf'))
                    if fraction < 1:
                        candidates = [t['params'] for t in results[:max(1, math.ceil(len(results)/self.budget['reduction_factor']))]]
        trials = self.trials[before:]
        full = [t for t in trials if t['fidelity'] == 1. and t['RMSE'] is not None]
        if not full: raise RuntimeError(f'No hay candidato válido a fidelidad completa: {label}')
        best = min(full, key=lambda t: (t['RMSE'], fingerprint(t['params'])))
        summary = {'method': method, 'best_params': best['params'], 'RMSE': best['RMSE'],
                   'sd_RMSE': best['sd_RMSE'], 'search_seconds': time.perf_counter()-clock,
                   'evaluated_configurations': len(trials), 'full_configurations': len(full),
                   'completed_fits': sum(s['status'] == 'completa' for t in trials for s in t['inner_folds']),
                   'failed_fits': sum(s['status'] != 'completa' for t in trials for s in t['inner_folds'])}
        self.summaries.append(summary)
        print(f'{self.key} {self.outer}: {method}, RMSE interno={best["RMSE"]:.6f}, {summary["search_seconds"]:.1f}s', flush=True)
        return summary

    def run(self):
        for method in METHODS: self.run_method(method)
        # Todos los finalistas tienen exactamente los mismos cinco folds y fidelidad1.
        # Empates numéricos <=1e-12 se resuelven por orden predefinido de métodos.
        optimum = min(s['RMSE'] for s in self.summaries)
        selected = next(s for s in self.summaries if s['RMSE'] <= optimum+1e-12)
        result = {'methods': self.summaries, 'selected_method': selected['method'],
                  'best_params': selected['best_params'], 'selection_rmse': selected['RMSE'],
                  'space': SPACES[self.key], 'budget': self.budget, 'evolution': self.evolution,
                  'outer': self.outer, 'trials_file': self.trial_file.name}
        (self.directory / f'selection_{self.key}_{self.outer}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        return result
