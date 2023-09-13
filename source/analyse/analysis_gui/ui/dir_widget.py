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
        Getter for cwd attribute. Returns the Path object of the current
        directory.
        '''
        return Path(self.edit.text())

    @cwd.setter
    def cwd(self, dirname:str|Path):
        '''
        Setter for cwd attribute. Sets/changes the current directory. dirname
        must be a directory, otherwise raises an exception.
        '''
        # if path is valid, resolve it (change to absolute path without ./
        # or ../, etc)
        if self.cwd.is_dir():
            self.edit.setText(str(Path(dirname).resolve()))
        else:
            raise NotADirectoryError('Directory does not exist or is invalid')

    @QtCore.pyqtSlot()
    def directoryChanged(self):
        '''
        Action to perform when the user edits the directory textbox.
        '''
        # set to cwd when the program is opened
        if self.edit.text() == '':
            self.cwd = Path.cwd()
        # if the path is invalid, change to last acceptable path and open
        # error popup
        else:
            try:
                self.cwd = self.edit.text()
            except NotADirectoryError as e:
                self.edit.undo()
                QtWidgets.QMessageBox.critical(self, 'Error',
                                               f'{type(e).__name__}: {e}')

    @QtCore.pyqtSlot()
    def chooseDirectory(self):
        '''
        Allows user to choose a directory using a menu. Sets self.cwd when
        finished.
        '''
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Open directory', self.edit.text(),
            options=QtWidgets.QFileDialog.Options()
        )
        if dirname:
            self.cwd = dirname
