# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

class ErrorWindow(QtWidgets.QWidget):
    '''
    UI of a popup that is displayed when an error occurs.
    '''
    def __init__(self, msg:str) -> None:
        '''
        Iniatiation method. Requires the owner AnalysisMainInterface
        instance to access its popup_open variable and a string to display as
        the error message.
        '''
        super().__init__()
        # QPixmap of the image of the error icon
        pixmap = QtGui.QPixmap(str(Path(__file__).parent/'error.png'))

        self.image = QtWidgets.QLabel(pixmap=pixmap, alignment=QtCore.Qt.AlignCenter)
        self.text = QtWidgets.QLabel(msg, alignment=QtCore.Qt.AlignCenter)
        self.text.setWordWrap(True)
        self.setWindowTitle("Error")

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.image)
        layout.addWidget(self.text)
