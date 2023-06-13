# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import subprocess
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
        uic.loadUi(Path(__file__).parent/'analysis_main.ui', self)
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
        self.analconv_radio = [self.analconv_box.itemAt(i).widget() \
                               for i in range(self.analconv_box.count())]

        # tab "Analyse Integrator"
        self.analint_push = self.findChild(QtWidgets.QPushButton, 'analint_push')
        self.analint_box = self.findChild(QtWidgets.QBoxLayout, 'analint_layout')
        self.analint_radio = [self.analint_box.itemAt(i).widget() \
                              for i in range(self.analint_box.count())]

        # tab "Analyse Results"
        self.analres_push = self.findChild(QtWidgets.QPushButton, 'analres_push')
        self.analres_box = self.findChild(QtWidgets.QBoxLayout, 'analres_layout')
        self.analres_radio = [self.analres_box.itemAt(i).widget() \
                              for i in range(self.analres_box.count())]

        # tab "Analyse System Evolution"
        self.analevol_push = self.findChild(QtWidgets.QPushButton, 'analevol_push')
        self.analevol_box = self.findChild(QtWidgets.QBoxLayout, 'analevol_layout')
        self.analevol_radio = [self.analevol_box.itemAt(i).widget() \
                               for i in range(self.analevol_box.count())]

        # tab "Analyse Potential Surface"
        self.analpes_push = self.findChild(QtWidgets.QPushButton, 'analpes_push')
        self.analpes_box = self.findChild(QtWidgets.QBoxLayout, 'analpes_layout')
        self.analpes_radio = [self.analpes_box.itemAt(i).widget() \
                               for i in range(self.analpes_box.count())]

    def _connectObjects(self) -> None:
        '''
        Connects named objects so they do stuff when interacted with.
        '''
        # line edit
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        # continue buttons. the lambda functions are required as .connect()
        # requires a function object as its parameter, but we also want to
        # set continuePushed's parameter in the meantime
        self.analconv_push.clicked.connect(lambda x: self.continuePushed(self.analconv_radio))
        self.analint_push.clicked.connect(lambda x: self.continuePushed(self.analint_radio))
        self.analres_push.clicked.connect(lambda x: self.continuePushed(self.analres_radio))
        self.analevol_push.clicked.connect(lambda x: self.continuePushed(self.analevol_radio))
        self.analpes_push.clicked.connect(lambda x: self.continuePushed(self.analpes_radio))

    @QtCore.pyqtSlot()
    def continuePushed(self, radio_buttons:list) -> None:
        '''
        Action to perform when the 'Continue' button is pushed, which requires
        a list of the corresponding QtWidgets.QRadioButton objects.
        '''
        wd = self.dir_edit.text()
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio_button.objectName() for radio_button in radio_buttons
                      if radio_button.isChecked()][0]
        match radio_name:
            case 'analconv_1': # check orthonormality of spfs in psi file
                self.runCmd(['ortho', '-i', wd], self.output_view)
            case 'analconv_2': # check orthonormality of spfs in restart file
                self.runCmd(['ortho', '-r', '-i', wd], self.output_view)
            case 'analconv_3': # plot populations of natural orbitals
                self.runCmd(['rdcheck', 'natpop', '1', '1', '-i', wd], self.output_view)
            case 'analconv_4': # plot populations of grid edges
                self.runCmd(['rdgpop', '-i', wd, '0'], self.output_view)
            case 'analconv_5': # plot time-evolution of norm of wavefunction
                self.runCmd(['norm', '-inter', '-i', wd], self.output_view)
            case 'analconv_6': # norm of wavefunction on restart file
                self.runCmd(['norm', '-r', '-i', wd], self.output_view)

            case 'analint_1': # analyse step size
                self.runCmd(['rdsteps', '-i', wd], self.output_view)
            case 'analint_2': # look at timing file
                self.runCmd(['cat', str(Path(wd)/'timing')], self.output_view)
            case 'analint_3': # type update file
                self.runCmd(['rdupdate', '-i', wd], self.output_view)
            case 'analint_4': # plot update step size
                self.runCmd(['rdupdate', '-inter', '-i', wd], self.output_view, '1')

            case 'analres_1': # plot autocorrelation function
                self.runCmd(['rdauto', '-inter', '-i', wd], self.output_view)
            # placeholder (13 17 ev 50 2) values for now
            case 'analres_2': # plot FT of autocorrelation function
                self.runCmd(['autospec', '-inter', '-FT', '-i', wd,
                             '13', '17', 'ev', '50', '2'], self.output_view)
            case 'analres_3': # plot spectrum from autocorrelation function
                self.runCmd(['autospec', '-inter', '-i', wd,
                             '13', '17', 'ev', '50', '2'], self.output_view)
            case 'analres_4': # plot eigenvalues from matrix diagonalisation
                self.runCmd(['rdeigval', '-inter', '-i', wd], self.output_view)

            case 'analevol_1': # plot 1d density evolution
                self.runCmd(['showd1d', '-inter', '-i', wd], self.output_view, '1')
            case 'analevol_2': # plot 2d density evolution
                self.runCmd(['showsys', '-i', wd], self.output_view)
            case 'analevol_3': # plot diabatic state population
                self.runCmd(['plstate', '-i', wd], self.output_view)

            case 'analpes_1': # plot potential energy surface
                self.runCmd(['showsys', '-pes', '-i', wd], self.output_view, '1')

            case _:
                self.showError(f'objectName {radio_name} unknown')

    @QtCore.pyqtSlot()
    def directoryChanged(self) -> None:
        '''
        Action to perfrom when the user edits the directory textbox.
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

    def showError(self, msg:str) -> None:
        '''
        Creates a popup window showing an error message.
        '''
        self.popup_open = True
        self.error_window = ErrorWindow(self, msg)
        self.error_window.show()

    def runCmd(self, args:list, output_view:QtWidgets.QTextEdit, inp:str = None) -> None:
        '''
        This function will run the shell command sent to it and either shows
        the result in the given QTextEdit or displays an error message. args
        should be a list represented by the command split by spaces, eg.
        ['ls', '-A', '/home/']. inp is an input string to feed to stdin after
        the command execution
        '''
        # output_view argument is used instead of self.output_view in case
        # we need to add multiple views in the future
        try:
            p = subprocess.run(args, universal_newlines=True, input=inp,
                               cwd=self.dir_edit.text(), timeout=10,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=True)
            output_view.setText(p.stdout)
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
