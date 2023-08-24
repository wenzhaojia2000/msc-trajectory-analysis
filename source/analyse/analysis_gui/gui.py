# -*- coding: utf-8 -*-
'''
@author: 19081417

Contains the function that runs the GUI Analysis application. Note, due to how
python treats packages, another file not in this directory or subdirectory
needs to import the openGui function from this file and execute it.
'''

import sys
from pathlib import Path

def openGui():
    '''
    Opens the quantics analysis GUI.
    '''
    if sys.version_info < (3, 10):
        raise OSError('This program requires python >= 3.10. If you are running '
                      'conda, check the environment.yml file in this folder.')
    # make sure the folder containing the analysis_gui package is in sys.path
    # (ie. %QUANTICS_DIR%/source/analyse/)
    cwd = str(Path(__file__).parents[1])
    if cwd not in sys.path:
        sys.path.append(cwd)
        print(f'Note: {cwd} appended to sys.path')

    from .ui import main_window
    app = main_window.QtWidgets.QApplication(sys.argv)
    # create and show the window
    window = main_window.AnalysisMain()
    window.show()
    # run the main Qt loop
    sys.exit(app.exec_())
