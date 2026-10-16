"""Integridad de los tres métodos nuevos, sin ejecutar búsquedas completas."""
import json
import unittest
import numpy as np
import pandas as pd

from entregable3 import FEATURES, GROUP, TARGET, OUTPUT, metrics
from evaluacion_nuevos_e3 import partitions
from modelos_clasicos import classic_pipeline
from tcr_xgboost_e3 import robustness, positive_weights, TCRXGBRegressor


class SelectedModelsTests(unittest.TestCase):
    def test_tcr_matches_reference_max_ratio(self):
        X = np.array([[0.,0.],[.2,.4],[.2,.4],[1.,1.]])
        y = np.array([1.,2.,3.,5.])
        yn = (y-y.min())/np.ptp(y)
        expected = [1/(1+max(abs(yn[i]-yn[j])/(np.linalg.norm(X[i]-X[j])+1e-7)
                            for j in range(len(y)))) for i in range(len(y))]
        np.testing.assert_allclose(robustness(X,y),expected,rtol=1e-12)
        np.testing.assert_array_equal(robustness(X,np.ones(4)),np.ones(4))

    def test_tcr_never_removes_rows_and_weights_lowest_robustness(self):
        r=np.array([.3,.1,.5,.2,.9])
        w=positive_weights(r,.4,.3)
        np.testing.assert_array_equal(w,[1.,.3,1.,.3,1.])
        self.assertTrue((w>0).all())
        np.testing.assert_array_equal(positive_weights(r,0,1),np.ones(5))
        with self.assertRaises(ValueError):
            positive_weights(r,.2,0)

    def test_unweighted_control_equals_original_pipeline_and_predict_does_not_refit(self):
        train,test,_,_=partitions()
        frame=train.iloc[:120]
        params={'modelo__n_estimators':10,'modelo__max_depth':2,'modelo__learning_rate':.03}
        m=TCRXGBRegressor(0.,1.,params).fit(frame[FEATURES],frame[TARGET])
        baseline=classic_pipeline('xgboost').set_params(**params).fit(frame[FEATURES],frame[TARGET])
        np.testing.assert_allclose(m.predict(test.iloc[:5][FEATURES]),baseline.predict(test.iloc[:5][FEATURES]),atol=0,rtol=0)
        before=m.robustness_.copy()
        m.predict(test.iloc[5:10][FEATURES])
        np.testing.assert_array_equal(before,m.robustness_)

    def test_available_results_reproduce_canonical_metrics_and_folds(self):
        found=0
        for key in ['tcr_xgboost','tabicl_v2','hrt_boost']:
            folder=OUTPUT/key
            if not (folder/'reporte.json').exists():
                continue
            found+=1
            report=json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
            frame=pd.read_csv(folder/'test_predictions.csv.gz')
            for metric,value in metrics(frame[TARGET],frame.prediccion).items():
                self.assertAlmostEqual(value,report['test'][metric],places=12)
            oof=pd.read_csv(folder/'train_predictions.csv.gz')
            self.assertEqual(len(frame),188)
            self.assertEqual(len(oof),1309)
            self.assertNotIn(GROUP,oof)
            np.testing.assert_array_equal(oof.fold,pd.read_csv(OUTPUT/'train.csv.gz').fold)
            self.assertTrue(all(row['shared_students']==0 for row in report['fold_audit']))
        if found==0:
            self.skipTest('Evaluaciones aún en curso.')

    def test_tabicl_configuration_is_local_frozen_and_keeps_outliers(self):
        from tabicl_modelo_e3 import new_estimator, CHECKPOINT, LocalTabICLRegressor
        from tabicl._sklearn.preprocessing import OutlierRemover
        model=new_estimator()
        self.assertFalse(model.allow_auto_download)
        self.assertEqual(model.checkpoint_version,CHECKPOINT)
        self.assertEqual(model.n_estimators,8)
        self.assertEqual(model.norm_methods,['none'])
        self.assertTrue(np.isinf(model.outlier_threshold))
        X=np.array([[0.,0.],[1.,2.],[1e9,1e12]])
        np.testing.assert_array_equal(OutlierRemover(threshold=float('inf')).fit_transform(X),X)
        stub=LocalTabICLRegressor()
        stub.model_=object()
        stub.context_X_=X
        stub.context_y_=np.arange(3.)
        self.assertNotIn('model_',stub.__getstate__())

    def test_hrt_uses_official_estimator_and_internal_preparation(self):
        from hrt_modelo_e3 import make_model, GRID
        from hrt_boost import HRTBoostingRegressor
        from sklearn.model_selection import ParameterGrid
        pipeline=make_model()
        self.assertIsInstance(pipeline.named_steps['modelo'],HRTBoostingRegressor)
        self.assertEqual(pipeline.named_steps['modelo'].min_points,80)
        self.assertEqual(len(list(ParameterGrid(GRID))),12)

    def test_serialized_pipelines_reproduce_full_test_predictions(self):
        import joblib
        _,test,_,_=partitions()
        for key in ['tcr_xgboost','tabicl_v2','hrt_boost']:
            folder=OUTPUT/key
            if not (folder/'reporte.json').exists():
                self.skipTest('Esperando las tres evaluaciones completas.')
            report=json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
            saved=pd.read_csv(folder/'test_predictions.csv.gz').prediccion.to_numpy(float)
            model=joblib.load(report['private_model'])
            np.testing.assert_allclose(model.predict(test[FEATURES]),saved,rtol=1e-12,atol=1e-12)


if __name__=='__main__':
    unittest.main()
