"""
Unit tests for the :mod:`openqml` :class:`QNode` class.
"""

import unittest
import logging as log
log.getLogger()
from openqml.plugins.default import frx, frz

import autograd

from openqml import numpy as np
from defaults import openqml as qm, BaseTest

def expZ(state):
    return np.abs(state[0]) ** 2 - np.abs(state[1]) ** 2

thetas = np.linspace(-2*np.pi, 2*np.pi, 7)

def rubbish_circuit(x):
    qm.Rot(x, 0.3, -0.2, [0])
    qm.SWAP([0, 1])
    return qm.expectation.PauliZ(0)

class BasicTest(BaseTest):
    """Qnode tests.
    """
    def setUp(self):
        self.qubit_dev1 = qm.device('default.qubit', wires=1)
        self.qubit_dev2 = qm.device('default.qubit', wires=2)

    def test_qnode_fail(self):
        "Tests that expected failures correctly raise exceptions."
        log.info('test_qnode_fail')
        qnode = qm.QNode(rubbish_circuit, self.qubit_dev2)
        params = np.random.randn(qnode.num_variables)
        qnode(params)

        # gradient_angle cannot handle more-than-one-parameter gates
        with self.assertRaisesRegex(ValueError, "only differentiate one-parameter gates"):
            res = qnode.gradient(params, method='A')

        # only order-1 and order-2 finite diff methods are available
        with self.assertRaisesRegex(ValueError, "Order must be 1 or 2"):
            qnode.gradient(params, method='F', order=3)

    def test_qnode_fanout(self):
        "Tests that qnodes can compute the correct function when the same parameter is used in multiple gates."
        log.info('test_qnode_fanout')

        def circuit(reused_param, other_param):
            qm.RX(reused_param, [0])
            qm.RZ(other_param, [0])
            qm.RX(reused_param, [0])
            return qm.expectation.PauliZ(0)

        f = qm.QNode(circuit, self.qubit_dev1)

        for reused_param in thetas:
            for theta in thetas:
                other_param = theta ** 2 / 11
                y_eval = f(reused_param, other_param)
                Rx = frx(reused_param)
                Rz = frz(other_param)
                zero_state = np.array([1.,0.])
                final_state = (Rx @ Rz @ Rx @ zero_state)
                y_true = expZ(final_state)
                self.assertAlmostEqual(y_eval, y_true, delta=self.tol)

if __name__ == '__main__':
    print('Testing OpenQML version ' + qm.version() + ', QNode class.')
    # run the tests in this file
    suite = unittest.TestSuite()
    for t in (BasicTest,):
        ttt = unittest.TestLoader().loadTestsFromTestCase(t)
        suite.addTests(ttt)

    unittest.TextTestRunner().run(suite)
