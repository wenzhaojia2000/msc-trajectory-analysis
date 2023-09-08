# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides the functionality for the directory
editor.
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore, uic

class DirectoryWidget(QtWidgets.QWidget):
    '''
    Provides a text edit and tool button to allow choosing the directory of
    where the GUI tries to find Quantics output files.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor method. Setup to make the widget work, including connecting
        objects.
        '''
        super().__init__(*args, **kwargs)
        uic.loadUi(Path(__file__).parent/'dir_widget.ui', self)
        # set icon for button
        self.button.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon)
        )
        # connect objects
        self.edit.editingFinished.connect(self.directoryChanged)
        self.button.clicked.connect(self.chooseDirectory)
        # set text in edit to be the current working directory
        self.directoryChanged()

    @property
    def cwd(self):
        '''
        Returns the Path object of the current directory.
        '''
        return Path(self.edit.text())

    @QtCore.pyqtSlot()
    def directoryChanged(self):
        '''
        Action to perform when the user edits the directory textbox. The
        entered value must be a directory, otherwise raises an error.
        '''
        # set to cwd when the program is opened or everything is deleted
        if self.edit.text() == '':
            self.edit.setText(str(Path.cwd()))
        # if the path is invalid, change to last acceptable path and open
        # error popup
        elif self.cwd.is_dir() is False:
            self.edit.undo()
            QtWidgets.QMessageBox.critical(self, 'Error',
                'NotADirectoryError: Directory does not exist or is invalid')
        # if path is valid, resolve it (change to absolute path without ./
        # or ../, etc)
        elif self.cwd.is_dir():
            self.edit.setText(str(self.cwd.resolve()))

    @QtCore.pyqtSlot()
    def chooseDirectory(self):
        '''
        Allows user to choose a directory using a menu. Sets self.edit
        (and thus self.cwd) when finished.
        '''
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Open directory', self.edit.text(),
            options=QtWidgets.QFileDialog.Options()
        )
        if dirname:
            self.edit.setText(dirname)
