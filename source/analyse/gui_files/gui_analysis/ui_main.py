# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
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
        # the title of the graph if title is set to 'automatic'. set through
        # default_title argument of self.changePlotTitle
        self.default_title = ""

    def findObjects(self) -> None:
        '''
        Finds objects from the loaded .ui file and set them as instance
        variables and sets some of their properties.
        '''
        self.dir_edit = self.findChild(QtWidgets.QLineEdit, 'dir_edit')
        self.dir_edit_dialog = self.findChild(QtWidgets.QToolButton, 'dir_edit_dialog')
        self.tab_widget = self.findChild(QtWidgets.QTabWidget, 'tab_widget')
        self.text = self.findChild(QtWidgets.QTextEdit, 'output_text')
        self.graph = self.findChild(QtWidgets.QWidget, 'output_plot')
        self.slider = self.findChild(QtWidgets.QSlider, 'output_slider')

        # set icon of the dir_edit_dialog
        self.dir_edit_dialog.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DirLinkIcon
        ))
        # set properties of output_graph
        self.graph.setBackground('w')
        self.graph.showGrid(x=True, y=True)
        # hide slider initially
        self.slider.hide()

        # additional options
        self.timeout = self.findChild(QtWidgets.QDoubleSpinBox, 'timeout_spinbox')
        self.title = self.findChild(QtWidgets.QLineEdit, 'title_edit')
        self.legend = self.findChild(QtWidgets.QCheckBox, 'legend_checkbox')
        self.grid = self.findChild(QtWidgets.QCheckBox, 'grid_checkbox')

    def connectObjects(self) -> None:
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        self.dir_edit_dialog.clicked.connect(self.chooseDirectory)
        self.title.editingFinished.connect(self.changePlotTitle)
        self.legend.stateChanged.connect(self.toggleLegend)
        self.grid.stateChanged.connect(self.toggleGrid)

    def showError(self, msg:str) -> None:
        '''
        Creates a popup window showing an error message.
        '''
        self.error_window = ErrorWindow(msg)
        self.error_window.show()

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
        elif Path(self.dir_edit.text()).is_dir() is False:
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

    @QtCore.pyqtSlot()
    def changePlotTitle(self, default_title:str=None) -> None:
        '''
        Changes the title of the graph. Sets it to the default title if
        custom title is set to Automatic. Change the default title using the
        default_title argument.
        '''
        if default_title is not None:
            self.default_title = default_title
        if self.title.text() == "":
            self.graph.setTitle(self.default_title, color='k', bold=True)
        else:
            self.graph.setTitle(self.title.text(), color='k', bold=True)

    @QtCore.pyqtSlot()
    def toggleLegend(self) -> None:
        '''
        Toggles the plot legend on and off, depending on the status of the show
        legend checkbox.
        '''
        # if legend already exists, this just returns the legend
        legend = self.graph.addLegend()
        if self.legend.isChecked():
            legend.show()
        else:
            legend.hide()

    @QtCore.pyqtSlot()
    def toggleGrid(self) -> None:
        '''
        Toggles the plot grid on and off, depending on the status of the show
        grid checkbox.
        '''
        if self.grid.isChecked():
            self.graph.showGrid(x=True, y=True)
        else:
            self.graph.showGrid(x=False, y=False)

    def resetPlot(self, switch_to_plot:bool=False) -> None:
        '''
        Resets the graph for replotting. Call this method before plotting
        something new. Optionally can switch the tab menu so users can see the
        new plot.
        '''
        self.graph.clear()
        self.graph.getPlotItem().enableAutoRange()
        self.graph.getAxis('bottom').setTicks(None)
        self.graph.getAxis('left').setTicks(None)
        self.toggleLegend()
        self.slider.hide()
        if switch_to_plot:
            self.tab_widget.setCurrentIndex(1)
