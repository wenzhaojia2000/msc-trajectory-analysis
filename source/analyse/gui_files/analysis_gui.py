# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import sys
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui, uic

class Ui(QtWidgets.QMainWindow):
    '''
    UI of the main program.
    '''
    def __init__(self) -> None:
        '''
        The method that is called when a Ui instance is initiated.
        '''
        # call the inherited class' __init__ method
        super().__init__()
        # load the .ui file (from the folder this .py file is in rather than
        # wherever this is executed)
        uic.loadUi(Path(__file__).parent/'analysis_gui.ui', self)
        # find objects from .ui file and give them a variable name
        self._findObjects()
        # connect signals to objects so they work
        self._connectObjects()
        # bool that records whether there is a popup open (if the code tries
        # to open a popup while there is already one open the program
        # segfaults!)
        self.popup_open = False
        # set text in dir_edit to be the current working directory
        self.directoryChanged()
        
    def _findObjects(self) -> None:
        '''
        Finds objects from the loaded .ui file and gives them names.
        '''
        self.dir_edit = self.findChild(QtWidgets.QLineEdit, 'dir_edit')
        self.output_view = self.findChild(QtWidgets.QTextEdit, 'output_view')
        
        # tab "Analyse Convergence"
        self.analconv_push = self.findChild(QtWidgets.QPushButton, 'analconv_push')
        self.analconv_box = self.findChild(QtWidgets.QBoxLayout, 'analconv_layout')
        self.analconv_radio = [self.analconv_box.itemAt(i).widget() for i in range(self.analconv_box.count())]
        
        # tab "Analyse Integrator"
        self.analint_push = self.findChild(QtWidgets.QPushButton, 'analint_push')
        self.analint_box = self.findChild(QtWidgets.QBoxLayout, 'analint_layout')
        self.analint_radio = [self.analint_box.itemAt(i).widget() for i in range(self.analint_box.count())]
        
        # tab "Analyse Results"
        self.analres_push = self.findChild(QtWidgets.QPushButton, 'analres_push')
        self.analres_box = self.findChild(QtWidgets.QBoxLayout, 'analres_layout')
        self.analres_radio = [self.analres_box.itemAt(i).widget() for i in range(self.analres_box.count())]
        
        # tab "Analyse System Evolution"
        self.analevol_push = self.findChild(QtWidgets.QPushButton, 'analevol_push')
        self.analevol_box = self.findChild(QtWidgets.QBoxLayout, 'analevol_layout')
        self.analevol_radio = [self.analevol_box.itemAt(i).widget() for i in range(self.analevol_box.count())]
        
        # tab "Analyse Potential Surface"
        self.analpes_push = self.findChild(QtWidgets.QPushButton, 'analpes_push')
        
    def _connectObjects(self) -> None:
        '''
        Connects named objects so they do stuff when interacted with.
        '''
        # line edit
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        # continue buttons. the lambda functions are required as .connect()
        # requires a function object as its parameter, but we also want to
        # set continue_pushed's parameter in the meantime
        self.analconv_push.clicked.connect(lambda x: self.continuePushed(self.analconv_radio))
        self.analint_push.clicked.connect(lambda x: self.continuePushed(self.analint_radio))
        self.analres_push.clicked.connect(lambda x: self.continuePushed(self.analres_radio))
        self.analevol_push.clicked.connect(lambda x: self.continuePushed(self.analevol_radio))

    @QtCore.pyqtSlot()
    def continuePushed(self, radio_buttons:list) -> None:
        '''
        Action to perform when the 'Continue' button is pushed, which requires
        a list of the corresponding QtWidgets.QRadioButton objects.
        '''
        for radio_button in radio_buttons:
            if radio_button.isChecked():
                print(radio_button.objectName())

    @QtCore.pyqtSlot()
    def directoryChanged(self) -> None:
        '''
        Action to perfrom when the user edits the directory textbox.
        '''
        # set to cwd when the program is opened or everything is deleted
        if self.dir_edit.text() == "":
            self.dir_edit.setText(str(Path.cwd()))
        # if the path is invalid, change to last acceptable path and open
        # error popup
        elif Path(self.dir_edit.text()).is_dir() == False and self.popup_open == False:
            self.popup_open = True
            self.error_window = ErrorWindow(self, "Directory does not exist or is invalid")
            self.error_window.show()
            self.dir_edit.undo()
        # if path is valid, resolve it (change to absolute path without ./
        # or ../, etc)
        elif Path(self.dir_edit.text()).is_dir():
            self.dir_edit.setText(str(Path(self.dir_edit.text()).resolve()))

class ErrorWindow(QtWidgets.QWidget):
    '''
    UI of a popup that is displayed when an error occurs.
    '''
    def __init__(self, ui:Ui, message:str) -> None:
        '''
        Iniatiation method. Requires the parent Ui instance (so we can change
        the Ui's popup_open variable) and a message to display.
        '''
        super().__init__()
        self.message = message
        self.parent = ui
        
        self.setWindowTitle("Error")
        self.resize(200, 100)
        self.image = str(Path(__file__).parent/'error.png')
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(pixmap=QtGui.QPixmap(self.image),
                                          alignment=QtCore.Qt.AlignCenter))
        layout.addWidget(QtWidgets.QLabel(self.message,
                                          alignment=QtCore.Qt.AlignCenter))
        
    def closeEvent(self, *args, **kwargs) -> None:
        '''
        Method to execute when the popup is closed.
        '''
        super().closeEvent(*args, **kwargs)
        self.parent.popup_open = False

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # create and show the form
    window = Ui()
    window.show()
    # run the main Qt loop
    sys.exit(app.exec_())
