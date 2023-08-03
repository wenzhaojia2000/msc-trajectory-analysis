# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
System' tab of the analysis GUI. A class instance of this should be included in
the main UI class.
'''

from pathlib import Path
import re
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisSystem(AnalysisTab):
    '''
    Defines functionality for the 'Analyse System' tab of the analysis GUI.
    '''
    def __init__(self, parent:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(parent=parent, push_name='analsys_push',
                         box_name='analsys_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box '1d density options'
        self.den1d_box = self.parent().findChild(QtWidgets.QGroupBox, 'den1d_box')
        self.den1d_dof = self.parent().findChild(QtWidgets.QSpinBox, 'den1d_dof')
        self.den1d_state = self.parent().findChild(QtWidgets.QSpinBox, 'den1d_state')
        # group box 'pes options'
        self.showpes_box = self.parent().findChild(QtWidgets.QGroupBox, 'showpes_box')
        self.showpes_type = self.parent().findChild(QtWidgets.QComboBox, 'showpes_type')
        self.showpes_state = self.parent().findChild(QtWidgets.QSpinBox, 'showpes_state')
        # hide box
        self.showpes_box.hide()

    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the update options box when certain result is selected
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        try:
            match radio_name:
                case 'analsys_1': # plot 1d density evolution
                    self.showd1d()
                case 'analsys_2': # plot 2d density evolution
                    self.runCmd('showsys')
                case 'analsys_3': # plot diabatic state population
                    self.runCmd('plstate')
                case 'analsys_4': # plot potential energy surface
                    self.showpes()
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.parent().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.parent(), 'Error', f'{type(e).__name__}: {e}')

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {0: self.den1d_box, 3: self.showpes_box}
        for radio, box in options.items():
            if self.radio[radio].isChecked():
                box.show()
            else:
                box.hide()

    def showd1d(self) -> None:
        '''
        Reads the file output of using showd1d -T, which is expected to be
        in the format, where each cell is a float,

        x.11    t.1    y1.11    y2.11
        x.12    t.1    y1.12    y2.12
        ...     ...    ...      ...
        x.1n    t.1    y1.1n    y2.1n

        x.21    t.2    y1.21    y2.21
        ...     ...    ...      ...
        x.2n    t.2    y1.2n    y2.2n
        ...
        x.mn    t.m    y1.mn    y2.mn

        where x is position, t is time, and y1, y2 are the real and imag parts
        of the spf. Any lines starting with "set" or "plot" are ignored.
        Empty lines between time intervals are not required. Time intervals
        t.1 ... t.m are expected to increase linearly upwards.

        Plots the density over position with a scroll bar to scroll through
        time.
        '''
        den1d_options = [
            'f' + str(self.den1d_dof.value()),
            's' + str(self.den1d_state.value())
        ]
        self.runCmd('showd1d', '-T', '-w', *den1d_options)

        # find filename of command output
        if self.den1d_state.value() == 1:
            filepath = Path(self.parent().dir_edit.text())/f'den1d_{den1d_options[0]}'
        else:
            filepath = Path(self.parent().dir_edit.text())/f'den1d_{"_".join(den1d_options)}'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.readFloats(f, 4, ignore_regex=r'^plot|^set')
            # split the matrix into chunks depending on its time column
            n_interval = np.unique(self.parent().data[:, 1]).size
            self.parent().data = np.split(self.parent().data, n_interval)
        if self.parent().keep_files.isChecked() is False:
            # delete intermediate file
            filepath.unlink()

        # add contents of showd1d.log to text view
        filepath = Path(self.parent().dir_edit.text())/'showd1d.log'
        if filepath.is_file():
            with open(filepath, mode='r', encoding='utf-8') as f:
                self.parent().text.appendPlainText(f'{"-"*80}\n{f.read()}')
            if self.parent().keep_files.isChecked() is False:
                filepath.unlink()

        # adjust slider properties, connect to showd1dChangePlot slot
        self.parent().slider.setMaximum(len(self.parent().data)-1)
        self.parent().slider.setSliderPosition(0)
        try:
            self.parent().slider.valueChanged.disconnect()
        except TypeError:
            # happens if slider has no connections
            pass
        finally:
            self.parent().slider.valueChanged.connect(self.showd1dChangePlot)
        # start plotting
        self.parent().resetPlot(True, animated=True)
        self.parent().setPlotLabels(title='1D density evolution',
                                    bottom=f'DOF {den1d_options[0]} (au)',
                                    left='Density',
                                    top=f't={self.parent().data[0][0][1]}')
        self.parent().graph.plot(self.parent().data[0][:, 0], self.parent().data[0][:, 2],
                                 name='Re(phi)', pen='r')
        self.parent().graph.plot(self.parent().data[0][:, 0], self.parent().data[0][:, 3],
                                 name='Im(phi)', pen='b')

    @QtCore.pyqtSlot()
    def showd1dChangePlot(self) -> None:
        '''
        Allows the user to move the slider to control time when using the
        showd1d analysis.
        '''
        data_items = self.parent().graph.listDataItems()
        slider_pos = int(self.parent().slider.value())
        if self.parent().data and len(data_items) == 2:
            re, im = data_items
            if re.name() == 'Re(phi)' and im.name() == 'Im(phi)':
                self.parent().setPlotLabels(
                    top=f't={self.parent().data[slider_pos][0][1]} fs'
                )
                re.setData(self.parent().data[slider_pos][:, 0],
                           self.parent().data[slider_pos][:, 2])
                im.setData(self.parent().data[slider_pos][:, 0],
                           self.parent().data[slider_pos][:, 3])

    def showpes(self):
        '''
        Reads the xyz file from the menu-driven output of showsys -pes.
        The menu entries that are navigated by this function are:
            10 (choose task)
            20 (coordinate selection, using popup for the time being)
            60 (choose state)
        The format of the xyz file should be
             x.1   y.1   z.1.1
             x.1   y.2   z.1.2
             ...   ...   ...
             x.1   y.n   z.1.n
             x.2   y.1   z.2.1
             ...   ...   ...
             x.m   y.n   z.m.n
        If only x is selected in coordinate selection then z does not appear
        and the function plots a 1D plot. Otherwise, the x, y, z coordinates
        are converted into a x, y vector and z matrix and a contour plot is
        shown. x.1 < x.2 < ... x.m and for contour plots, the same for y,
        otherwise it won't work.
        '''
        # if a plot file already exists, this won't work as we can't type
        # the option to overwrite.
        filepath = Path(self.parent().dir_edit.text())/'pes.xyz'
        filepath.unlink(missing_ok=True)

        inp = ''
        # choose task (10)
        inp += {0: '10\n2\n', 1: '10\n1\n'}[self.showpes_type.currentIndex()]
        # choose state (60), plot one state only (1)
        inp += f'60\n1\n{self.showpes_state.value()}\n'
        # choose coordinates (20)
        # temporary popup to get information for now. will need to read input
        # to get mode names and add gui radio buttons + spinbox for each mode
        coords, ok = QtWidgets.QInputDialog.getMultiLineText(
            self.parent(),
            'Input coordinates',
            'Write one mode on each line, with its name (not index!) then '
            'either x, y, or value'
        )
        if not ok:
            raise ValueError('User cancelled operation')
        inp += f'20\n{coords}\n0\n'
        # save data to xyz file (5), enter name, then exit (0)
        inp += '5\npes.xyz\n0'
        # run the command
        self.runCmd('showsys', '-pes', input=inp)

        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.readFloats(f)
        if self.parent().keep_files.isChecked() is False:
            # delete intermediate file
            filepath.unlink()

        # start plotting
        self.parent().resetPlot(switch_to_plot=True)
        if self.parent().data.shape[1] == 3:
            # contour plot
            # convert from list xyz coordinate data to grid data
            x = np.unique(self.parent().data[:, 0])
            y = np.unique(self.parent().data[:, 1])
            z = np.array(self.parent().data[:, 2]).reshape(x.shape[0], y.shape[0])
            self.parent().setPlotLabels(title=self.showpes_type.currentText(),
                                        bottom='DOF x (au)', left='DOF y (au)')
            self.parent().plotContours(x, y, z, 21)
        else:
            # line plot
            self.parent().setPlotLabels(title=self.showpes_type.currentText(),
                                        bottom='DOF x (au)', left='PES')
            self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 1],
                                     name='PES', pen='r')
