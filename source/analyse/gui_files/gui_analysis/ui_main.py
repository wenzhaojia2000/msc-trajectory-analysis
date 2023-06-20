# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import subprocess
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, uic

from .ui_base import AnalysisBase
from .ui_error import ErrorWindow
from .analysis_convergence import AnalysisConvergence
from .analysis_integrator import AnalysisIntegrator
from .analysis_results import AnalysisResults
from .analysis_system import AnalysisSystem

class AnalysisMain(QtWidgets.QMainWindow, AnalysisBase):
    '''
    UI of the main program.
    '''
    def __init__(self) -> None:
        '''
        The method that is called when a Ui instance is initiated.
        '''
        # call the inherited classes' __init__ method
        super().__init__()
        # load the .ui file (from the folder this .py file is in rather than
        # wherever this is executed)
        uic.loadUi(Path(__file__).parent/'ui_analysis.ui', self)
        # find objects from .ui file and give them a variable name
        self.findObjects()
        # connect signals to objects so they work
        self.connectObjects()

        # bool that records whether there is a popup open (if the code tries
        # to open a popup while there is already one open the program
        # segfaults!)
        self.popup_open = False
        # set text in dir_edit to be the current working directory
        self.directoryChanged()

        # the program is futher composed of classes which dictate
        # function for each analysis tab
        self.convergence = AnalysisConvergence(self)
        self.integrator = AnalysisIntegrator(self)
        self.results =  AnalysisResults(self)
        self.system = AnalysisSystem(self)

    def findObjects(self) -> None:
        '''
        Finds objects from the loaded .ui file and set them as instance
        variables.
        '''
        self.dir_edit = self.findChild(QtWidgets.QLineEdit, 'dir_edit')
        self.dir_edit_dialog = self.findChild(QtWidgets.QToolButton, 'dir_edit_dialog')
        self.output_view = self.findChild(QtWidgets.QTextEdit, 'output_view')

        # set icon of the dir_edit_dialog
        self.dir_edit_dialog.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DirLinkIcon
        ))

    def connectObjects(self) -> None:
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        self.dir_edit_dialog.clicked.connect(self.chooseDirectory)

    @QtCore.pyqtSlot()
    def directoryChanged(self) -> None:
        '''
        Action to perform when the user edits the directory textbox.
        '''
        # set to cwd when the program is opened or everything is deleted
        if self.dir_edit.text() == '':
            self.dir_edit.setText(str(Path.cwd()))
        # if the path is invalid, change to last acceptable path and open
        # error popup
        elif Path(self.dir_edit.text()).is_dir() is False and self.popup_open is False:
            self.showError('Directory does not exist or is invalid')
            self.dir_edit.undo()
        # if path is valid, resolve it (change to absolute path without ./
        # or ../, etc)
        elif Path(self.dir_edit.text()).is_dir():
            self.dir_edit.setText(str(Path(self.dir_edit.text()).resolve()))

    @QtCore.pyqtSlot()
    def chooseDirectory(self) -> None:
        '''
        Allows user to choose a directory using a menu when the directory
        button is clicked.
        '''
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Open directory', self.dir_edit.text(),
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly
        )
        if dirname:
            self.dir_edit.setText(dirname)

    def showError(self, msg:str) -> None:
        '''
        Creates a popup window showing an error message.
        '''
        self.popup_open = True
        self.error_window = ErrorWindow(self, msg)
        self.error_window.show()

    def runCmd(self, *args, input_=None) -> None:
        '''
        This function will run the shell command sent to it and either shows
        the result in the output's text tab or displays an error message. args
        should be a series of strings with commas representing spaces, eg.
        'ls', '-A', '/home/'. The keyword input_ is the a string to feed to
        stdin after the command execution.
        '''
        try:
            p = subprocess.run(args, universal_newlines=True, input=input_,
                               cwd=self.dir_edit.text(), timeout=10,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=True)
            self.output_view.setText(p.stdout)
        except subprocess.CalledProcessError as e:
            self.showError(f'Error (CalledProcessError): {e}'
                           f'\n\n{e.stdout}')
        except subprocess.TimeoutExpired as e:
            self.showError(f'Error (TimeoutExpired): {e}'
                           f'\n\n{e.stdout}')
        except FileNotFoundError:
            self.showError('Error (FileNotFoundError)'
                           '\n\nThis error is likely caused by a quantics program '
                           'not being installed or being in an invalid directory.')
        except Exception as e:
            self.showError(f'Error ({type(e)})'
                           f'\n\n{e}')
