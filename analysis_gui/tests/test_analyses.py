# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the class that provides unit testing for various analysis methods.
See run_tests.py for more info.
'''

from pathlib import Path
import sys
import re
import unittest
import numpy as np
from ..ui import main_window

class TestAnalyses(unittest.TestCase):
    '''
    Tests various python-implemented analysis methods.
    '''

    def setUp(self):
        '''
        The method to execute before running a test procedure.
        '''
        self.app = main_window.QtWidgets.QApplication(sys.argv)
        self.window = main_window.AnalysisMain()
        self.fixtures_dir = Path(__file__).parent/'fixtures'

    def testrdtiming(self):
        '''
        Tests the sorting functionality of the AnalysisIntegrator.rdtiming
        method (first three sorts only)
        '''
        self.window.dir.edit.setText(str(self.fixtures_dir.resolve()))
        self.window.analint.radio[1].click()

        # test sort by subroutine name
        self.window.analint.timing_sort.setCurrentIndex(0)
        self.window.analint.analyse.click()
        output = self.window.text.toPlainText()
        expected_order = ['AddHunPhi', 'CalcOPs', 'DBread', 'Density',
                          'Dicht1Phi', 'Funkr', 'GWP overlap', 'GenDVR',
                          'GenOPER', 'Gh_elements', 'Gh_elems: LHA',
                          'Gh_elems: kinet', 'Gh_elems: sum', 'Gwp_Gdot',
                          'Gwp_Ymat', 'HPhi', 'Hlochphi', 'HunPhi', 'Importho',
                          'Init_WF', 'Mfields', 'Output', 'PhiHPhi',
                          'PhiHunPhi', 'Project', 'PropWF', 'RK5', 'Setgwpdyn',
                          'Setgwpdyn1ms', 'subgdot1']
        regex = r'.+?'.join(expected_order)
        self.assertTrue(bool(re.search(regex, output, re.DOTALL)))

        # test sort by calls
        self.window.analint.timing_sort.setCurrentIndex(1)
        self.window.analint.analyse.click()
        output = self.window.text.toPlainText()
        expected_order = ['1578830', '255285', '68076', '51057', '18025',
                          '17020', '17019', '17019', '17019', '17019', '17019',
                          '17019', '17019', '17019', '17019', '17019', '17019',
                          '17019', '2122', '2121', '201', '1', '1', '1', '1', '1']
        regex = r'.+?'.join(expected_order)
        self.assertTrue(bool(re.search(regex, output, re.DOTALL)))

        # test sort by cpu/call
        self.window.analint.timing_sort.setCurrentIndex(2)
        self.window.analint.analyse.click()
        output = self.window.text.toPlainText()
        expected_order = ['140668.6200', '693.4628', '16.3360', '15.9800',
                          '15.7120', '8.2426', '7.8470', '2.3965', '1.4055',
                          '0.3090', '0.3089', '0.0927', '0.0784', '0.0431',
                          '0.0396', '0.0395', '0.0265', '0.0120', '0.0081',
                          '0.0003', '0.0002', '0.0001', '0.0001', '0.0001',
                          '0.0001', '0.0001', '0.0001', '0.0000', '0.0000',
                          '0.0000']
        regex = r'.+?'.join(expected_order)
        self.assertTrue(bool(re.search(regex, output, re.DOTALL)))

    def testcalcrate(self):
        '''
        Tests the AnalysisDirectDynamics.calcrate method.
        '''
        self.window.dir.edit.setText(str(self.fixtures_dir.resolve()))
        self.window.analdd.radio[0].click()
        self.window.analdd.analyse.click()
        # only testing a fraction of the total data for now
        # numpy array of the 'y' data up to the 39th data
        obtained = self.window.plot.listDataItems()[0].getData()[1][:39]
        expected = [0, 1, 2, 3, 2, 0, 0, 2, 2, 3, 3, 4, 2, 3, 2, 5, 3, 5, 5, 3,
                    8, 1, 5, 10, 3, 5, 10, 3, 3, 3, 6, 4, 5, 6, 3, 6, 9, 4, 7]
        self.assertTrue(np.array_equal(obtained, expected))

    @unittest.skip('Not yet implemented')
    def testddpesgeo(self):
        '''
        Tests the AnalysisDirectDynamics.ddpesgeo method.
        '''
        raise NotImplementedError

    def tearDown(self):
        '''
        The method to execute after executing a test procedure.
        '''
        self.window.close()
        self.app.quit()
        del self.app

