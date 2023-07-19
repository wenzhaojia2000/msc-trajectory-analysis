# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import sys
from gui_analysis import ui_main

if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise OSError('This program requires python >= 3.10. If you are running '
                      'conda, check the environment.yml file in this folder.')

    app = ui_main.QtWidgets.QApplication(sys.argv)
    # create and show the window
    window = ui_main.AnalysisMain()
    window.show()
    # run the main Qt loop
    sys.exit(app.exec_())
