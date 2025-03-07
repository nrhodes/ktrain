#!/usr/bin/env python3
"""
Tests of ktrain text classification flows
"""
import sys
import os
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID";
os.environ["CUDA_VISIBLE_DEVICES"]="0"
sys.path.insert(0,'../..')
import IPython
from unittest import TestCase, main, skip
import numpy as np
import ktrain
from ktrain import graph as gr

class TestNodeClassification(TestCase):


    def test_cora(self):
        
        (trn, val, preproc, 
        df_holdout, G_complete)  = gr.graph_nodes_from_csv(
                                                            'graph_data/cora/cora.content', 
                                                             'graph_data/cora/cora.cites',  
                                                             sample_size=20, 
                                                             holdout_pct=0.1, holdout_for_inductive=True,
                                                            train_pct=0.1, sep='\t')


        
        learner = ktrain.get_learner(model=gr.graph_node_classifier('graphsage', trn,), 
                             train_data=trn, 
                             #val_data=val, 
                             batch_size=64)


        lr = 0.01
        hist = learner.autofit(lr, 10)

        # test training results
        self.assertAlmostEqual(max(hist.history['lr']), lr)
        self.assertGreater(max(hist.history['acc']), 0.9)


        # test top losses
        obs = learner.top_losses(n=1, val_data=val)
        self.assertIn(obs[0][0], list(range(val.targets.shape[0])))
        learner.view_top_losses(preproc=preproc, n=1, val_data=val)

        # test weight decay
        self.assertEqual(len(learner.get_weight_decay()), 1)
        self.assertEqual(learner.get_weight_decay()[0], None)
        learner.set_weight_decay(1e-4)
        self.assertAlmostEqual(learner.get_weight_decay()[0], 1e-4)

        # test load and save model
        learner.save_model('/tmp/test_model')
        learner.load_model('/tmp/test_model')

        # test validate
        learner.validate(val_data=val)
        cm = learner.validate(val_data=val)
        print(cm)
        for i, row in enumerate(cm):
            self.assertEqual(np.argmax(row), i)

        # test predictor
        p = ktrain.get_predictor(learner.model, preproc)
        self.assertIn(p.predict_transductive(val.ids[0:1])[0], preproc.get_classes())
        p.predict_transductive(val.ids[0:1])
        p.save('/tmp/test_predictor')
        p = ktrain.load_predictor('/tmp/test_predictor')
        self.assertIn(p.predict_transductive(val.ids[0:1])[0], preproc.get_classes())

if __name__ == "__main__":
    main()
