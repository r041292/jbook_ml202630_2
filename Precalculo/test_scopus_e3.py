"""Integración, particiones, predicciones y serialización de métodos Scopus."""
from io import BytesIO
import unittest
from pathlib import Path
import warnings
import ast

import joblib
import numpy as np
from sklearn.base import clone
from threadpoolctl import threadpool_limits

from entregable3 import FEATURES,TARGET,GROUP,CATEGORICAL,NUMERIC
from evaluacion_nuevos_e3 import partitions
from modelos_scopus_e3 import make_model
from entregable3 import BOOK


class TestScopus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train,cls.test,cls.folds,_=partitions()

    def test_groups_and_predictors(self):
        self.assertEqual(len(FEATURES),15)
        self.assertNotIn(TARGET,FEATURES)
        self.assertNotIn(GROUP,FEATURES)
        self.assertNotIn('nota_final',FEATURES)
        self.assertFalse(set(self.train[GROUP]) & set(self.test[GROUP]))
        for fi,va in self.folds:
            self.assertFalse(set(self.train.iloc[fi][GROUP]) & set(self.train.iloc[va][GROUP]))

    def test_comparison_fix_preserves_training(self):
        original=ast.parse((BOOK/'resultados/e3/scopus/evaluador_entrenamiento_original.py').read_text(encoding='utf-8'))
        current=ast.parse((BOOK/'evaluar_scopus_e3.py').read_text(encoding='utf-8'))
        functions=lambda tree:{n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        a,b=functions(original),functions(current)
        for name in ['fit','predict','tune','provenance']:
            self.assertEqual(ast.dump(a[name]),ast.dump(b[name]))
        # Desde la construcción de OOF hasta la exportación, run permanece idéntico.
        def training_tail(node):
            index=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='oof' for t in n.targets))
            return ast.dump(ast.Module(body=node.body[index:],type_ignores=[]))
        self.assertEqual(training_tail(a['run']),training_tail(b['run']))

    def test_estimators_roundtrip_and_mechanisms(self):
        frame=self.train.iloc[:150]
        unseen=self.train.iloc[150:160][FEATURES].copy()
        unseen[CATEGORICAL[0]]='CATEGORIA_NO_VISTA'
        configs={'xbart':dict(trees=10,depth=2,leaf=10),'catboost':dict(iterations=10,depth=2),
                 'kernel_ridge':dict(alpha=1.,gamma=.01),'copilot':dict(depth=2,leaf=10,alpha=.5)}
        for key,params in configs.items():
            with self.subTest(key=key),warnings.catch_warnings(),threadpool_limits(limits=1):
                warnings.simplefilter('ignore',UserWarning)
                model=clone(make_model(key,**params)).fit(frame[FEATURES],frame[TARGET])
                pred=model.predict(unseen)
                self.assertEqual(pred.shape,(10,))
                self.assertTrue(np.isfinite(pred).all())
                buffer=BytesIO()
                joblib.dump(model,buffer)
                buffer.seek(0)
                np.testing.assert_allclose(joblib.load(buffer).predict(unseen),pred,atol=1e-10,rtol=0)
                prep=model.named_steps['preprocesamiento']
                estimator=model.named_steps['modelo']
                if key=='copilot':
                    trees=estimator.model_.pilot_trees
                    self.assertEqual(len(trees),2)
                    np.testing.assert_allclose(pred,np.mean([t.predict(prep.transform(unseen)) for t in trees],axis=0))
                    np.testing.assert_array_equal(trees[0].categorical,np.arange(len(NUMERIC),15))
                elif key=='xbart':
                    draws=estimator.model_.predict(prep.transform(unseen),terms='y_hat',type='posterior')
                    self.assertEqual(draws.shape,(10,60))
                    np.testing.assert_allclose(pred,draws[:,20:].mean(axis=1))
                elif key=='kernel_ridge':
                    self.assertAlmostEqual(estimator.transformer_.mean_[0],frame[TARGET].mean())
                else:
                    self.assertEqual(estimator.model_.get_param('boosting_type'),'Ordered')


if __name__=='__main__':unittest.main()
