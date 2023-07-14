# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import shutil
import subprocess

from PyQt5 import QtWidgets, QtCore
from pyqtgraph.exporters import ImageExporter

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

        # set properties of the plot graph
        self.tweakGraph()
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
        self.timeout_menu = self.findChild(QtWidgets.QMenu, 'timeout_menu')
        self.menu_dir = self.findChild(QtWidgets.QAction, 'menu_dir')
        self.keep_files = self.findChild(QtWidgets.QAction, 'keep_files_checkbox')

        # set icon of the dir_edit_dialog
        self.dir_edit_dialog.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DirLinkIcon
        ))
        # hide slider initially
        self.slider.hide()

    def connectObjects(self) -> None:
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        self.dir_edit_dialog.clicked.connect(self.chooseDirectory)
        self.menu_dir.triggered.connect(self.chooseDirectory)

        # add a timeout spinbox to the timeout menu
        self.timeout_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.timeout_spinbox.setSuffix(' s')
        self.timeout_spinbox.setMaximum(86400)
        self.timeout_spinbox.setValue(60)
        self.timeout_spinbox.setDecimals(1)
        timeout_action = QtWidgets.QWidgetAction(self)
        timeout_action.setDefaultWidget(self.timeout_spinbox)
        self.timeout_menu.addAction(timeout_action)

    def tweakGraph(self) -> None:
        '''
        Sets the properties of self.graph, the pyqtgraph widget. Adds custom
        menus to the pyqtgraph context menu, which is opened when right-
        clicking on the graph.
        '''
        self.graph.setBackground('w')
        self.graph.showGrid(x=True, y=True)
        # remove the top axis and tick marks, so adding a label to the top axis
        # looks like a subtitle
        self.graph.getAxis('top').setPen((0, 0, 0, 0))
        self.graph.getAxis('top').setStyle(tickLength=0, showValues=False)
        # these are the default menus that come with pyqtplot
        # context_menu: the menu that pops up when right click on plot
        # plot_menu: the submenu in the context_menu called 'plot options'
        context_menu = self.graph.getPlotItem().vb.menu
        plot_menu = self.graph.getPlotItem().ctrlMenu

        # save video action (off by default)
        self.save_video = context_menu.addAction("Save video")
        self.save_video.triggered.connect(self.saveVideo)
        self.save_video.setVisible(False)
        # custom title action
        plot_menu.addSeparator()
        title_menu = plot_menu.addMenu("Custom title")
        self.title_edit = QtWidgets.QLineEdit(self)
        self.title_edit.setPlaceholderText('Automatic')
        self.title_edit.setMinimumWidth(180)
        self.title_edit.editingFinished.connect(self.changePlotTitle)
        title_action = QtWidgets.QWidgetAction(self)
        title_action.setDefaultWidget(self.title_edit)
        title_menu.addAction(title_action)
        # show legend action
        self.legend_checkbox = plot_menu.addAction("Show Legend")
        self.legend_checkbox.setCheckable(True)
        self.legend_checkbox.setChecked(True)
        self.legend_checkbox.triggered.connect(self.toggleLegend)

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
            options=QtWidgets.QFileDialog.Options()
        )
        if dirname:
            self.dir_edit.setText(dirname)

    @QtCore.pyqtSlot()
    def changePlotTitle(self, default_title:str=None) -> None:
        '''
        Changes the title of the graph, by setting it to the default title if
        custom title is set to Automatic, or whatever the user wrote otherwise.
        '''
        if self.title_edit.text() == '':
            self.graph.setTitle(self.default_title, color='k', bold=True)
        else:
            self.graph.setTitle(self.title_edit.text(), color='k', bold=True)

    @QtCore.pyqtSlot()
    def toggleLegend(self) -> None:
        '''
        Toggles the plot legend on and off, depending on the status of the show
        legend checkbox.
        '''
        # if legend already exists, this just returns the legend
        legend = self.graph.addLegend()
        if self.legend_checkbox.isChecked():
            legend.show()
        else:
            legend.hide()

    @QtCore.pyqtSlot()
    def saveVideo(self) -> None:
        '''
        Saves an .mp4 file of the current plot (which should be animated with
        slider control). Requires ffmpeg installed on the command line.
        '''
        # make sure user has ffmpeg installed
        try:
            subprocess.run(['ffmpeg', '-version'], check=False)
        except FileNotFoundError:
            self.showError('Please install ffmpeg to call this function.')
            return None
        except subprocess.SubprocessError as e:
            self.owner.showError(f'Error ({e.__class__.__name__}): {e}'
                                 f'\n\n{e.stdout}')
            return None
        # obtain a savename for the file
        savename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
            "Save File", self.dir_edit.text() + '/Untitled.mp4',
            "Video (*.mp4);;All files (*)"
        )
        if savename == "":
            # user cancels operation
            return None
        # add .mp4 suffix to savename if not already
        savename = str(Path(savename).with_suffix('.mp4'))
        # create a temporary directory in the same folder as chosen
        temp_directory = Path(savename).parent/'frames'
        temp_directory.mkdir(parents=True, exist_ok=True)

        # export image for each frame, into the temporary directory
        exporter = ImageExporter(self.graph.plotItem)
        for i in range(self.slider.minimum(), self.slider.maximum()+1):
            self.slider.setSliderPosition(i)
            exporter.export(str(temp_directory/f'{i:05}.png'))
            # force pyqt to update slider immediately, so user can see progress
            self.slider.repaint()

        # run ffmpeg to generate video https://stackoverflow.com/questions/24961127
        args = ['ffmpeg', '-y', '-framerate', '30', '-pattern_type', 'glob', '-i',
                '*.png', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(savename)]
        subprocess.run(args, cwd=temp_directory, check=True)
        # delete the temporary folder
        shutil.rmtree(temp_directory)
        return None

    def resetPlot(self, switch_to_plot:bool=False, animated:bool=False) -> None:
        '''
        Resets the graph for replotting. Call this method before plotting
        something new. Use switch_to_plot to switch the tab menu so users can
        see the new plot. Use animated to enable the slider and 'save video'
        options to prepare for an animated plot.
        '''
        self.graph.clear()
        self.graph.getPlotItem().enableAutoRange()
        self.graph.setLabels(top='', bottom='', left='')
        self.graph.getAxis('bottom').setTicks(None)
        self.graph.getAxis('left').setTicks(None)
        self.toggleLegend()
        if animated:
            self.slider.show()
            self.save_video.setVisible(True)
        else:
            self.slider.hide()
            self.save_video.setVisible(False)
        if switch_to_plot:
            self.tab_widget.setCurrentIndex(1)

    def setPlotLabels(self, **kwargs) -> None:
        '''
        Sets the plot title using the title=... keyword and axis labels using
        left=..., right=..., top=...

        Use this function instead of self.graph.setLabels() to still allow the
        user to customise the plot title (by calling self.changePlotTitle
        instead of self.graph.setTitle).
        '''
        for key, value in kwargs.items():
            if key == 'title':
                self.default_title = value
                self.changePlotTitle()
            else:
                if isinstance(value, str):
                    value = (value,)
                self.graph.setLabel(key, *value, color='k')
