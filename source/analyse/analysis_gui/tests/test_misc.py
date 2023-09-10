# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the class that provides unit testing for miscellaneous methods
(ones that are not performing analyses). See run_tests.py for more info.
'''

from pathlib import Path
from time import perf_counter
import sys
import unittest
import numpy as np
from ..ui import main_window

class TestConvenienceMethods(unittest.TestCase):
    '''
    Tests the AnalysisTab.readFloats and CustomTextWidget.writeTable methods.
    AnalysisTab.runCmd not tested since that would essentially be a test of the
    subprocess module.
    '''
    # parameters to generate a file with a grid of random numbers
    N_COLUMNS = 5
    N_ROWS = 20000

    def setUp(self):
        '''
        The method to execute before running a test procedure.
        '''
        # open a main window, no need to show it though
        self.app = main_window.QtWidgets.QApplication(sys.argv)
        self.window = main_window.AnalysisMain()
        # generate random floats with mantissa between -1 and 1, exponent
        # (base 2) between -32 and 32. this way some will numbers will be
        # expressed in scientific notation but others will be expressed
        # normally. used to test readFloats
        self.grid = np.ldexp(np.random.uniform(-1, 1, (self.N_ROWS, self.N_COLUMNS)),
                             np.random.randint(-32, 32, (self.N_ROWS, self.N_COLUMNS)))
        # save to file
        self.filename = Path(__file__).parent/'grid.txt'
        with open(self.filename, mode='w', encoding='utf-8') as s:
            for row in self.grid:
                for cell in row:
                    s.write(f'{cell}     ')
                s.write('\n')

    def testReadFloats(self):
        '''
        Tests the readFloats method in the AnalysisMain class.
        '''
        with open(self.filename, mode='r', encoding='utf-8') as f:
            # time how long it takes to read floats
            time = perf_counter()
            # using analconv but could use any analysis tab
            read_grid = self.window.analconv.readFloats(f, floats_per_line=self.N_COLUMNS)
            print(f'[INFO] Reading {self.N_ROWS}*{self.N_COLUMNS} grid '
                  f'took {perf_counter() - time} s')
        self.assertTrue(np.array_equal(read_grid, self.grid))

    def testWriteTable(self):
        '''
        Tests that the readFloats method can successfully reproduce the
        original grid after the writeTable method in the CustomTextWidget
        class writes the grid into the text widget.

        Note: CustomTextWidget can only store so much data, so making N_ROWS
        and/or N_COLUMNS too high will segfault the program.
        '''
        self.window.text.writeTable(self.grid)
        read_grid = self.window.analconv.readFloats(
            self.window.text.toPlainText().split('\n')
        )
        # since write table only has limited precision must use approximation
        self.assertTrue(np.allclose(read_grid, self.grid))

    def tearDown(self):
        '''
        The method to execute after executing a test procedure.
        '''
        self.filename.unlink()
        self.window.close()
        self.app.quit()
        # required to prevent some errors with python's auto garbage collection
        del self.app
