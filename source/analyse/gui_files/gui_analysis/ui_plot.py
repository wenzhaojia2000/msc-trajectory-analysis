# -*- coding: utf-8 -*-
"""
@author: 19081417

Consists of the single class that provides the functionality for the plot
widget.
"""

from pathlib import Path
import shutil
import subprocess

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5 import QtWidgets, QtCore, QtGui

class CustomPlotWidget(pg.PlotWidget):
    '''
    Extends the capabilities of pyqtgraph's PlotWidget, allowing the user to
    customise the title, toggle the legend, save an animated plot, and plot
    a contour graph.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor method.
        
        For the widget to work, requires the following to be present in
        self.window():
            - self.window().data
            - self.window().speed
            - QSlider self.window().scrubber
            - QLineEdit self.window().dir_edit (and self.window().cwd)
            - QTabWidget self.window().tab_widget
        '''
        super().__init__(*args, **kwargs)
        # the title of the graph if title is set to 'automatic'. set using
        # self.setLabels(title=...)
        self.default_title = ''

        # editing PlotWidget properties
        self.setBackground('w')
        self.showGrid(x=True, y=True)
        # remove the top axis and tick marks, so adding a label to the top axis
        # looks like a subtitle
        self.getAxis('top').setPen((0, 0, 0, 0))
        self.getAxis('top').setStyle(tickLength=0, showValues=False)
        # these are the default menus that come with pyqtplot
        # context_menu: the menu that pops up when right click on plot
        # plot_menu: the submenu in the context_menu called 'plot options'
        context_menu = self.getPlotItem().vb.menu
        plot_menu = self.getPlotItem().ctrlMenu

        # save .npy file
        self.save_npy = context_menu.addAction("Save .npy data")
        self.save_npy.triggered.connect(self.saveData)
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
        # colourbar that is displayed for contour plots. it's supposed to
        # be used for image plots only, but plotContours uses it. we pass an
        # empty ImageItem to its image parameter instead. you can also change
        # the colourmap here. to find different ones execute
        #   pyqtgraph.examples.run()
        # and select the Colors -> Color Maps option.
        self.colourmap = pg.colormap.get('CET-R4')
        self.colourbar = self.getPlotItem().addColorBar(
            pg.ImageItem(), colorMap=self.colourmap, interactive=False
        )
        # hide until a contour plot is plotted
        self.colourbar.hide()

    @QtCore.pyqtSlot()
    def changePlotTitle(self):
        '''
        Changes the title of the graph, by setting it to the default title if
        custom title is set to Automatic, or whatever the user wrote otherwise.
        '''
        if self.title_edit.text() == '':
            self.setTitle(self.default_title, color='k', bold=True)
        else:
            self.setTitle(self.title_edit.text(), color='k', bold=True)

    @QtCore.pyqtSlot()
    def toggleLegend(self):
        '''
        Toggles the plot legend on and off, depending on the status of the show
        legend checkbox.
        '''
        # if legend already exists, this just returns the legend
        legend = self.addLegend()
        if self.legend_checkbox.isChecked():
            legend.show()
        else:
            legend.hide()

    @QtCore.pyqtSlot()
    def saveData(self):
        '''
        Saves the array or numpy array present in self.window().data into a
        numpy (.npy) file.
        '''
        if self.window().data is None:
            QtWidgets.QMessageBox.information(
                self, 'No data', 'No data have been plotted yet.'
            )
            return None
        # obtain a savename for the file
        savename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
            "Save File", str(self.window().cwd / 'Untitled.npy'),
            "Numpy file (*.npy);;All files (*)"
        )
        if not ok:
            # user cancels operation
            return None
        # if the savename already exists np.save does not overwrite, but
        # appends to file. just change this by removing it if it exists
        Path(savename).unlink(missing_ok=True)
        np.save(savename, self.window().data)
        QtWidgets.QMessageBox.information(
            self, 'Success', 'Save data successful.'
        )
        return None

    @QtCore.pyqtSlot()
    def saveVideo(self):
        '''
        Saves an .mp4 file of the current plot (which should be animated with
        slider control). Requires ffmpeg installed on the command line.
        '''
        # make sure user has ffmpeg installed
        try:
            subprocess.run(['ffmpeg', '-version'], check=False)
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(self, 'Error',
                'FileNotFoundError: Please install ffmpeg to call this function.')
            return None
        # obtain a savename for the file
        savename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
            "Save File", str(self.window().cwd / 'Untitled.mp4'),
            "Video (*.mp4);;All files (*)"
        )
        if not ok:
            # user cancels operation
            return None
        # add .mp4 suffix to savename if not already
        savename = str(Path(savename).with_suffix('.mp4'))
        # create a temporary directory in the same folder as chosen
        temp_directory = Path(savename).parent/'frames'
        temp_directory.mkdir(parents=True, exist_ok=True)

        # change cursor to wait cursor
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # export image for each frame, into the temporary directory
        exporter = pg.exporters.ImageExporter(self.plotItem)
        for i in range(self.window().scrubber.minimum(), self.window().scrubber.maximum()+1):
            self.window().scrubber.setSliderPosition(i)
            exporter.export(str(temp_directory/f'{i:05}.png'))
            # force pyqt to update slider immediately, so user can see progress
            self.window().scrubber.repaint()
        QtWidgets.QApplication.restoreOverrideCursor()

        # run ffmpeg to generate video https://stackoverflow.com/questions/24961127
        # no error if height not divisible by 2 https://stackoverflow.com/questions/20847674/
        args = ['ffmpeg', '-y', '-framerate', str(self.window().speed),
                '-pattern_type', 'glob', '-i', '*.png', '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', '-vf',
                'pad=ceil(iw/2)*2:ceil(ih/2)*2:color=white', str(savename)]
        try:
            subprocess.run(args, cwd=temp_directory, check=True)
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.critical(self, 'Error',
                f'{e.__class__.__name__}: {e} At the moment of this error, the '
                f'console output was:\n\n{e.stdout}')
            return None
        # delete the temporary folder
        shutil.rmtree(temp_directory)
        QtWidgets.QMessageBox.information(
            self, 'Success', 'Save video successful.'
        )
        return None

    def reset(self, switch_to_plot:bool=False, animated:bool=False):
        '''
        Resets the graph for replotting. Call this method before plotting
        something new. Use switch_to_plot to switch the tab menu so users can
        see the new plot. Use animated to enable the media player and 'save
        video' options to prepare for an animated plot.
        '''
        self.clear()
        self.getPlotItem().enableAutoRange()
        self.setLabels(top='', bottom='', left='')
        self.getAxis('bottom').setTicks(None)
        self.getAxis('left').setTicks(None)
        self.colourbar.hide()
        self.toggleLegend()
        if animated:
            self.window().media_box.show()
            self.save_video.setVisible(True)
        else:
            self.window().media_box.hide()
            self.save_video.setVisible(False)
        if switch_to_plot:
            self.window().tab_widget.setCurrentIndex(1)

    def setLabels(self, **kwargs):
        '''
        Sets the default plot title using the title=... keyword and axis labels
        using left=..., right=..., top=...

        Overrides the existing self.setLabels to still allow the user to
        customise the plot title (by calling self.changePlotTitle instead of
        self.setTitle).
        '''
        for key, value in kwargs.items():
            if key == 'title':
                self.default_title = value
                self.changePlotTitle()
            else:
                if isinstance(value, str):
                    value = (value,)
                self.setLabel(key, *value, color='k')

    def plotContours(self, x:np.array, y:np.array, z:np.array, levels:int|list):
        '''
        Given numpy arrays x with shape (N,), y with shape (M,) and z with
        shape (M, N), plots a contour graph. Shows a colourbar to the side.

        If levels is an integer, plots n_level contour lines with levels
        ranging from min(z) to max(z). If it is a list, the contour lines are
        plotted for the levels given in the list.
        '''
        if isinstance(levels, int):
            levels = np.linspace(z.min(), z.max(), levels)
        colours = self.colourmap.getLookupTable(nPts=len(levels), mode=pg.ColorMap.QCOLOR)
        # a single contour line is known as an isocurve in pyqtgraph. it does
        # not accept x or y values, only the data (z). to display it properly
        # we need to transform it using QtGui.QTransform first.
        tr = QtGui.QTransform()
        tr.translate(x.min(), y.min())
        tr.scale((x.max() - x.min()) / np.shape(z)[0],
                 (y.max() - y.min()) / np.shape(z)[1])
        # create the isocurves, transforming each one
        for i in range(len(levels)):
            c = pg.IsocurveItem(data=z, level=levels[i], pen=colours[i])
            c.setTransform(tr)
            self.getPlotItem().addItem(c)
        self.colourbar.setLevels((levels[0], levels[-1]))
        self.colourbar.show()
