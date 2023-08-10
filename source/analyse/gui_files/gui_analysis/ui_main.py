# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides the functionality for the main
window, including menus and the directory edit.
'''

from pathlib import Path
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from .ui_base import AnalysisBase, AnalysisMeta
from .ui_plot import CustomPlotWidget
from .analysis_convergence import AnalysisConvergence
from .analysis_integrator import AnalysisIntegrator
from .analysis_results import AnalysisResults
from .analysis_system import AnalysisSystem
from .analysis_directdynamics import AnalysisDirectDynamics

class AnalysisMain(AnalysisBase, QtWidgets.QMainWindow, metaclass=AnalysisMeta):
    '''
    UI of the main program.

    Also consists of functions for plotting to the UI's graph and for writing
    to the UI's text screen.
    '''
    def __init__(self):
        '''
        The method that is called when a Ui instance is initiated.
        '''
        # call the inherited class' __init__ method
        super().__init__()
        # load the .ui file (from the folder this .py file is in rather than
        # wherever this is executed)
        uic.loadUi(Path(__file__).parent/'ui_analysis.ui', self)
        # activate analysis tabs. these classes dictate functionality for each
        # analysis tab
        for class_, object_name in zip(
                [AnalysisConvergence, AnalysisIntegrator, AnalysisResults,
                 AnalysisSystem, AnalysisDirectDynamics],
                ['analconv_tab', 'analint_tab', 'analres_tab',
                 'analsys_tab', 'analdd_tab']
            ):
            self.findChild(class_, object_name)._activate()
        # set a main window icon. try to find the PsiPhi file in doc/graphics
        # (from file location, go up 4 folders for the main quantics directory)
        icon = Path(__file__).parents[4]/'doc/graphics/PsiPhi_logo.png'
        self.setWindowIcon(QtGui.QIcon(str(icon)))

        self.findObjects()
        self.connectObjects()
        # set properties of the text view and plot graph
        self.tweakText()
        # set text in dir_edit to be the current working directory
        self.directoryChanged()
        # data which may be displayed by the window, and may or may not be
        # interacted with by some its widgets
        self.data = None

    def findObjects(self):
        '''
        Finds objects from the loaded .ui file and set them as instance
        variables and sets some of their properties.
        '''
        # ui items
        self.dir_edit = self.findChild(QtWidgets.QLineEdit, 'dir_edit')
        self.dir_edit_dialog = self.findChild(QtWidgets.QToolButton, 'dir_edit_dialog')
        self.tab_widget = self.findChild(QtWidgets.QTabWidget, 'tab_widget')
        self.text = self.findChild(QtWidgets.QPlainTextEdit, 'output_text')
        self.graph = self.findChild(CustomPlotWidget, 'output_plot')
        self.slider = self.findChild(QtWidgets.QSlider, 'output_slider')
        # menu items
        self.timeout_menu = self.findChild(QtWidgets.QMenu, 'timeout_menu')
        self.exit = self.findChild(QtWidgets.QAction, 'action_exit')
        self.menu_dir = self.findChild(QtWidgets.QAction, 'menu_dir')
        self.cleanup = self.findChild(QtWidgets.QAction, 'cleanup')
        self.no_command = self.findChild(QtWidgets.QAction, 'no_command')

        # set icon of the dir_edit_dialog
        self.dir_edit_dialog.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DirLinkIcon
        ))
        # hide slider initially
        self.slider.hide()

    def connectObjects(self):
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        self.dir_edit_dialog.clicked.connect(self.chooseDirectory)
        self.menu_dir.triggered.connect(self.chooseDirectory)
        self.exit.triggered.connect(lambda x: self.close())
        self.cleanup.triggered.connect(self.cleanupDirectory)

        # add a timeout spinbox to the timeout menu
        self.timeout_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.timeout_spinbox.setSuffix(' s')
        self.timeout_spinbox.setMaximum(86400)
        self.timeout_spinbox.setValue(60)
        self.timeout_spinbox.setDecimals(1)
        timeout_action = QtWidgets.QWidgetAction(self)
        timeout_action.setDefaultWidget(self.timeout_spinbox)
        self.timeout_menu.addAction(timeout_action)

    def tweakText(self):
        '''
        Sets the additional actions of a custom menu in the text tab, which is
        opened when right-clicking on the text view. When the context menu is
        requested, these actions are added into the menu.
        '''
        self.save_text = QtWidgets.QAction('Save text')
        self.save_text.triggered.connect(self.saveText)
        self.line_wrap = QtWidgets.QAction('Line Wrap')
        self.line_wrap.setCheckable(True)
        self.line_wrap.triggered.connect(self.changeLineWrap)
        self.text.customContextMenuRequested.connect(self.showTextMenu)

    @property
    def cwd(self):
        '''
        Returns the Path object of the current directory.
        '''
        return Path(self.dir_edit.text())

    @QtCore.pyqtSlot()
    def directoryChanged(self):
        '''
        Action to perform when the user edits the directory textbox.
        '''
        # set to cwd when the program is opened or everything is deleted
        if self.dir_edit.text() == '':
            self.dir_edit.setText(str(Path.cwd()))
        # if the path is invalid, change to last acceptable path and open
        # error popup
        elif Path(self.dir_edit.text()).is_dir() is False:
            self.dir_edit.undo()
            QtWidgets.QMessageBox.critical(self, 'Error',
                'NotADirectoryError: Directory does not exist or is invalid')
        # if path is valid, resolve it (change to absolute path without ./
        # or ../, etc)
        elif Path(self.dir_edit.text()).is_dir():
            self.dir_edit.setText(str(Path(self.dir_edit.text()).resolve()))

    @QtCore.pyqtSlot()
    def chooseDirectory(self):
        '''
        Allows user to choose a directory using a menu when the directory
        button is clicked.
        '''
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Open directory', self.dir_edit.text(),
            options=QtWidgets.QFileDialog.Options()
        )
        if dirname:
            self.dir_edit.setText(dirname)

    @QtCore.pyqtSlot()
    def cleanupDirectory(self):
        '''
        Asks the user whether to delete any output files associated with
        analysis quantics programs (not from quantics itself), eg. trajectory
        from gwptraj, gpop.pl from rdgpop. If so, removes them.
        '''
        # glob-type filenames to remove
        file_glob = [
            'den1d_*',
            'trajectory',
            # pl files
            'gpop.pl',
            'spectrum.pl',
            # log files
            'gwptraj.log',
            'showd1d.log',
            # xyz files
            'pes.xyz',
        ]
        # find the output files actually present in the directory
        files = []
        for glob in file_glob:
            files.extend(list(self.cwd.glob(glob)))

        if files:
            clicked = QtWidgets.QMessageBox.question(
                self, 'Delete these files?', 'These files will be deleted:\n' +\
                '\n'.join([file.name for file in files])
            )
            if clicked == QtWidgets.QMessageBox.Yes:
                for file in files:
                    file.unlink()
                QtWidgets.QMessageBox.information(
                    self, 'Success', 'Deletion successful.'
                )
        else:
            QtWidgets.QMessageBox.information(
                self, 'No files found',
                'Found no analysis output files in this directory.'
            )

    @QtCore.pyqtSlot(QtCore.QPoint)
    def showTextMenu(self, point):
        '''
        Shows a custom context menu when right-clicking on the text view.
        '''
        # create a standard menu (with copy and select all) and add to it
        text_menu = self.text.createStandardContextMenu(point)
        # when right-clicked, add the extra actions in tweakText and show the
        # menu at the point (mapToGlobal to translate to where window is)
        text_menu.exec_(
            text_menu.actions() + [self.save_text, self.line_wrap],
            self.text.mapToGlobal(point)
        )

    @QtCore.pyqtSlot()
    def saveText(self):
        '''
        Saves an .txt file of the current text in the text view.
        '''
        # obtain a savename for the file
        savename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
            "Save File", self.dir_edit.text() + '/Untitled.txt',
            "Text (*.txt);;All files (*)"
        )
        if not ok:
            # user cancels operation
            return None
        with open(savename, mode='w', encoding='utf-8') as s:
            s.write(self.text.toPlainText())
        QtWidgets.QMessageBox.information(
            self, 'Success', 'Save text successful.'
        )

    @QtCore.pyqtSlot()
    def changeLineWrap(self):
        '''
        Changes the line wrapping in the text view.
        '''
        if self.line_wrap.isChecked():
            self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        else:
            self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

    def writeTable(self, table:list, header:list=None, colwidth:int=16,
                   pre:str=None, post:str=None):
        '''
        Function that writes a table (list of lists or tuples) into a formatted
        table written into self.text.

        Ensure strings and integers are less than the column width (floats are
        automatically formatted to be fixed width). The default width is 16
        with 1 space of padding.

        header is a list of column names which is shown above the table. pre
        and post are strings that are printed before and after the table,
        respectively.
        '''
        if colwidth < 8:
            raise ValueError('colwidth cannot be lower than 8')
        # obtain border length, the number of hyphens to section off
        if len(table) > 0:
            border_len = len(table[0]) * (colwidth + 1)
        elif header:
            border_len = len(header) * (colwidth + 1)
        else:
            border_len = 0

        self.text.clear()
        if pre:
            self.text.appendPlainText(pre)
        self.text.appendPlainText('-'*border_len)
        # print header, wrapped by hyphens
        if header:
            header = ''.join([f'{{:>{colwidth}}} '.format(col) for col in header])
            self.text.appendPlainText(header)
            self.text.appendPlainText('='*border_len)
        # print out results
        for row in table:
            out = ''
            for cell in row:
                if isinstance(cell, float) and np.isfinite(cell):
                    # scientific format with 9 dp (8 dp if |exponent| > 100)
                    if abs(cell) >= 1e+100 or 0 < abs(cell) <= 1e-100:
                        out += f'{{: .{colwidth-8}e}} '.format(cell)
                    else:
                        out += f'{{: .{colwidth-7}e}} '.format(cell)
                else:
                    # align right with width 16 (str() allows None to be formatted)
                    out += f'{{:>{colwidth}}} '.format(str(cell))
            self.text.appendPlainText(out)
        # show bottom border only if there is at least one result
        if len(table) > 0:
            self.text.appendPlainText('-'*border_len)
        if post:
            self.text.appendPlainText(post)
