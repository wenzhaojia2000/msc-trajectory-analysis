# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import re
import subprocess
from pathlib import Path

import numpy as np
from PyQt5 import QtWidgets, QtCore

from .ui_base import AnalysisMainInterface
from .ui_error import ErrorWindow
from .analysis_convergence import AnalysisConvergence
from .analysis_integrator import AnalysisIntegrator
from .analysis_results import AnalysisResults
from .analysis_system import AnalysisSystem

class AnalysisMain(QtWidgets.QMainWindow, AnalysisMainInterface):
    '''
    UI of the main program.
    '''
    def __init__(self) -> None:
        '''
        The method that is called when a Ui instance is initiated.
        '''
        # find absolute path to the .ui file (so it won't look whereever the
        # script was run)
        ui_file = Path(__file__).parent/'ui_analysis.ui'
        # call the inherited classes' __init__ method with the location of the
        # ui file
        super().__init__(ui_file=ui_file)

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
        variables and sets some of their properties.
        '''
        self.dir_edit = self.findChild(QtWidgets.QLineEdit, 'dir_edit')
        self.dir_edit_dialog = self.findChild(QtWidgets.QToolButton, 'dir_edit_dialog')
        self.output_text = self.findChild(QtWidgets.QTextEdit, 'output_text')
        self.output_graph = self.findChild(QtWidgets.QWidget, 'output_plot')

        # set icon of the dir_edit_dialog
        self.dir_edit_dialog.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DirLinkIcon
        ))
        # set properties of output_graph
        self.output_graph.setBackground('w')
        self.output_graph.showGrid(x=True, y=True)

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

    def runCmd(self, *args, input_:str=None) -> str:
        '''
        This function will run the shell command sent to it and either returns
        and shows the result in the output's text tab or displays an error
        message (in which case None is returned).

        args should be a series of strings with commas representing spaces, eg.
        'ls', '-A', '/home/'. The keyword input_ is the a string to feed to
        stdin after the command execution.
        '''
        try:
            p = subprocess.run(args, universal_newlines=True, input=input_,
                               cwd=self.dir_edit.text(), timeout=10,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=True)
            self.output_text.setText(p.stdout)
            return p.stdout
        except subprocess.CalledProcessError as e:
            self.showError(f'Error (CalledProcessError): {e}'
                           f'\n\n{e.stdout}')
            return None
        except subprocess.TimeoutExpired as e:
            self.showError(f'Error (TimeoutExpired): {e}'
                           f'\n\n{e.stdout}')
            return None
        except FileNotFoundError:
            self.showError('Error (FileNotFoundError)'
                           '\n\nThis error is likely caused by a quantics program '
                           'not being installed or being in an invalid directory.')
            return None
        except Exception as e:
            self.showError(f'Error ({e.__class__.__name__})'
                           f'\n\n{e}')
            return None

    def plotFromText(self, text:str, title:str="", xlabel:str="", ylabel:str="",
                     labels:list=None) -> None:
        '''
        Plots a graph into self.output_plot from the given text in the format

        x.1    y1.1    y2.1    ...    yn.1
        x.2    y1.2    y2.2    ...    yn.2
        ...    ...     ...     ...    ...
        x.m    y1.m    y2.m    ...    yn.m

        where each cell is in a numeric form that can be converted into a float 
        like 0.123 or 1.234E-10, etc., and cells are seperated with any number
        of spaces (or tabs).

        The title, xlabel, ylabel, and legend entries (labels) of the graph
        can also be set. If labels is None (not set), the legend will not be
        shown.
        '''
        # overcomplicated regex to match floats
        # [+-]?                   optionally a + or - at the beginning
        # \d+(?:\.\d*)?           a string of digits, optionally with decimal
        #                         point and possibly more digits
        # (?:[eE][+-]?\d+)?       optionally an exponential (e+N, e-N) at the
        #                         end
        # \.\d+                   catches floats that start with decimal like
        #                         .25
        # [+-]?inf|nan            catches weird values like +-inf and nan
        float_regex = re.compile(
            r'([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+|[+-]?inf|nan)'
        )
        arr = []
        row_shape = 0
        for line in text.split('\n'):
            # find all floats in the line
            matches = re.findall(float_regex, line)
            # add to list if at least one is found
            if matches:
                # make sure length of rows are consistent. set row_shape from
                # first non-empty row and exit if found to be non-consistent
                if len(arr) == 0:
                    row_shape = len(matches)
                    # probably not going to happen but i only have so many
                    # colours to choose from
                    if row_shape > 7:
                        self.showError('Error (ValueError)'
                                       '\n\nToo many lines to plot!')
                        return None
                elif len(matches) != row_shape:
                    print('[AnalysisMain.plotFromText] Attempted to plot invalid text')
                    return None
                # regex returns strings, need to convert into float
                arr.append(list(map(float, matches)))

        arr = np.array(arr)
        # no floats found: text is likely something else eg. a bunch of text
        # like "cannot open or read update file". in which case, don't plot
        # anything
        if arr.size == 0:
            print('[AnalysisMain.plotFromText] I wasn\'t given any values to plot')
            return None
        # make sure there's a label for each column if it is given
        if labels is not None and len(labels) != arr.shape[1] - 1:
            self.showError('Error (ValueError)'
                           '\n\n[AnalysisMain.plotFromText] Number of labels '
                           'given does not match number of lines to plot')
            return None

        # colours for different lines
        colours = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
        self.output_plot.setLabel("left", ylabel, color='k')
        self.output_plot.setLabel("bottom", xlabel, color='k')
        self.output_plot.setTitle(title, color='k', bold=True)
        self.output_plot.addLegend()
        # plot a line for each row after the first (which are the x values)
        for j in range(1, arr.shape[1]):
            if labels is None:
                self.output_plot.plot(arr[:, 0], arr[:, j], pen=colours[j-1])
            else:
                self.output_plot.plot(arr[:, 0], arr[:, j], name=labels[j-1],
                                      pen=colours[j-1])
        return None
