# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import sys
from ui import ui_analysis_main as ui_analysis

if __name__ == '__main__':
    app = ui_analysis.QtWidgets.QApplication(sys.argv)

    # create and show the form
    window = ui_analysis.Ui()
    window.show()
    # run the main Qt loop
    sys.exit(app.exec_())
