# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import sys
from gui_analysis import ui_main

if __name__ == '__main__':
    app = ui_main.QtWidgets.QApplication(sys.argv)

    # create and show the form
    window = ui_main.AnalysisMain()
    window.show()
    # run the main Qt loop
    sys.exit(app.exec_())
