# -*- coding: utf-8 -*-
'''
@author: 19081417

Opens the Quantics analysis GUI application. If the flag '-test' is appended to
the end while running this script with python, runs the tests instead.

Usage: (Replace python3 with your the name of your python executable.)
    python3 quantics_analysis_gui.py
    python3 quantics_analysis_gui.py -test
'''

from pathlib import Path
import sys

# make sure the folder containing the analysis_gui package is in sys.path
# (ie. %QUANTICS_DIR%/source/analyse/)
cwd = str(Path(__file__).parent)
if cwd not in sys.path:
    sys.path.append(cwd)
    print(f'Note: {cwd} appended to sys.path')

if '-test' in sys.argv:
    from analysis_gui.tests import run_tests
    run_tests.runTests()
else:
    from analysis_gui import gui
    gui.openGui()
