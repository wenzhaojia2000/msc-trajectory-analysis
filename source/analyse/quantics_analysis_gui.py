# -*- coding: utf-8 -*-
'''
@author: 19081417

Opens the GUI Analysis application.
'''

from pathlib import Path
import sys

# make sure the folder containing the analysis_gui package is in sys.path
# (ie. %QUANTICS_DIR%/source/analyse/)
cwd = str(Path(__file__).parent)
if cwd not in sys.path:
    sys.path.append(cwd)
    print(f'Note: {cwd} appended to sys.path')

from analysis_gui import gui
gui.openGui()
