# -*- coding: utf-8 -*-
'''
@author: 19081417

Opens the GUI Analysis application.
'''

import sys
from pathlib import Path
from gui_analysis import ui_main

if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise OSError('This program requires python >= 3.10. If you are running '
                      'conda, check the environment.yml file in this folder.')
    # make sure this folder is added to sys.path, or pyqt will fail to find
    # the promoted widgets' file locations
    cdir = str(Path(__file__).parent)
    if cdir not in sys.path:
        sys.path.append(cdir)
        print(f'Note: {cdir} appended to sys.path')

    app = ui_main.QtWidgets.QApplication(sys.argv)
    # create and show the window
    window = ui_main.AnalysisMain()
    window.show()
    # run the main Qt loop
    sys.exit(app.exec_())
