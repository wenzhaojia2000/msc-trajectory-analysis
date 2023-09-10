# -*- coding: utf-8 -*-
'''
@author: 19081417

Runs all tests in the current folder (python files starting with 'test_').

Due to how python packages work, individual test files cannot be tested using
the unittest command line API. Instead, you can run this file using python.
'''

import unittest
from pathlib import Path

def runTests():
    '''
    Runs the tests in the this folder (analysis_gui.tests).
    '''
    loader = unittest.TestLoader()
    tests = loader.discover('analysis_gui.tests',
                            pattern='test_*.py',
                            # run from directory above analysis_gui
                            top_level_dir=Path(__file__).parents[2])
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)

if __name__ == '__main__':
    runTests()
