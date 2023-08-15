# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
System' tab of the analysis GUI. A class instance of this should be included in
the main UI class.
'''

import re
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisTab
from .ui_coordselect import CoordinateSelector

class AnalysisSystem(AnalysisTab):
    '''
    Promoted widget that defines functionality for the 'Analyse System' tab of
    the analysis GUI.
    '''
    def _activate(self):
        '''
        Activation method. See the documentation in AnalysisTab for more
        information.
        '''
        super()._activate(push_name='analsys_push', layout_name='analsys_layout',
                          options={
                              0: 'den1d_box', 1: 'den2d_box', 3: 'showpes_box'
                          })

    def findObjects(self, push_name:str, box_name:str):
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box '1d density options'
        self.den1d_dof = self.findChild(QtWidgets.QSpinBox, 'den1d_dof')
        self.den1d_state = self.findChild(QtWidgets.QSpinBox, 'den1d_state')
        # group box '2d density options'
        self.den2d_state = self.findChild(QtWidgets.QSpinBox, 'den2d_state')
        self.den2d_coord_box = self.findChild(QtWidgets.QScrollArea, 'den2d_coord_box')
        self.den2d_coord = self.findChild(CoordinateSelector, 'den2d_coord')
        # group box 'pes options'
        self.showpes_type = self.findChild(QtWidgets.QComboBox, 'showpes_type')
        self.showpes_state = self.findChild(QtWidgets.QSpinBox, 'showpes_state')
        self.showpes_coord_box = self.findChild(QtWidgets.QScrollArea, 'showpes_coord_box')
        self.showpes_coord = self.findChild(CoordinateSelector, 'showpes_coord')

    @QtCore.pyqtSlot()
    def optionSelected(self):
        '''
        Shows per-analysis options in a QGroupBox if a valid option is checked.
        '''
        super().optionSelected()
        if self.radio[1].isChecked():
            self.den2d_coord.refresh()
            # allow the scroll area to resize up to a maximum size. extra +2
            # because scroll bar appears otherwise (for some reason)
            self.den2d_coord_box.setFixedHeight(
                2 + min(self.den2d_coord.height(), 130)
            )
        if self.radio[3].isChecked():
            self.showpes_coord.refresh()
            self.showpes_coord_box.setFixedHeight(
                2 + min(self.showpes_coord.height(), 130)
            )

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self):
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
                    self.showd2d()
                case 'analsys_3': # plot diabatic state population
                    self.runCmd('statepop')
                case 'analsys_4': # plot potential energy surface
                    self.showpes()
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.window().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.window(), 'Error', f'{type(e).__name__}: {e}')

    def showd1d(self):
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
            filepath = self.window().cwd/f'den1d_{den1d_options[0]}'
        else:
            filepath = self.window().cwd/f'den1d_{"_".join(den1d_options)}'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f, 4, ignore_regex=r'^plot|^set')
            # split the matrix into chunks depending on its time column
            n_interval = np.unique(self.window().data[:, 1]).size
            self.window().data = np.split(self.window().data, n_interval)

        # add contents of showd1d.log to text view
        filepath = self.window().cwd/'showd1d.log'
        if filepath.is_file():
            with open(filepath, mode='r', encoding='utf-8') as f:
                self.window().text.appendPlainText(f'{"-"*80}\n{f.read()}')

        # adjust scrubber properties, connect to showd1dChangePlot slot
        self.window().scrubber.setMaximum(len(self.window().data)-1)
        self.window().scrubber.setSliderPosition(0)
        try:
            self.window().scrubber.valueChanged.disconnect()
        except TypeError:
            # happens if scrubber has no connections
            pass
        finally:
            self.window().scrubber.valueChanged.connect(self.showd1dChangePlot)
        # start plotting
        self.window().graph.reset(switch_to_plot=True, animated=True)
        self.window().graph.setLabels(title='1D density evolution',
                                      bottom=f'DOF {den1d_options[0]} (au)',
                                      left='Density',
                                      top=f't={self.window().data[0][0][1]}')
        self.window().graph.plot(self.window().data[0][:, 0], self.window().data[0][:, 2],
                                 name='Re(phi)', pen='r')
        self.window().graph.plot(self.window().data[0][:, 0], self.window().data[0][:, 3],
                                 name='Im(phi)', pen='b')

    @QtCore.pyqtSlot()
    def showd1dChangePlot(self):
        '''
        Allows the user to move the scrubber to control time when using the
        showd1d analysis.
        '''
        re, im = self.window().graph.listDataItems()
        scrubber_pos = int(self.window().scrubber.value())
        self.window().graph.setLabels(
            top=f't={self.window().data[scrubber_pos][0][1]} fs'
        )
        re.setData(self.window().data[scrubber_pos][:, 0],
                   self.window().data[scrubber_pos][:, 2])
        im.setData(self.window().data[scrubber_pos][:, 0],
                   self.window().data[scrubber_pos][:, 3])

    def showd2d(self):
        '''
        Reads the xyz file from the menu-driven output of showsys -nopes, with
        the default task of 'plot diabatic reduced density'.
        The menu entries that are navigated by this function are:
            20 (coordinate selection)
            60 (choose state)
        The format of the xyz file should be
             x.1   y.1   z.1.1.1
             x.1   y.1   z.1.1.2
             ...   ...   ...
             x.1   y.n   z.1.1.n
             x.2   y.1   z.1.2.1
             ...   ...   ...
             x.m   y.n   z.1.m.n
                                           (Two empty lines here to seperate
                                            time intervals)
             x.1   y.1   z.2.1.1           (Repeat for timestep 2)
             ...   ...   ...               (etc. until tfinal)

        The x and y values should be the same for all intervals, and x.1 < x.2
        < ... x.m with same for y.

        Unfortunately a 'time' column is not included here unlike with the
        1D density, so it will have to be gathered from the input file -- not
        implemented yet.
        '''
        # if a plot file already exists, this won't work as we can't type
        # the option to overwrite.
        filepath = self.window().cwd/'den2d.xyz'
        filepath.unlink(missing_ok=True)

        coords = str(self.den2d_coord)
        if not coords:
            # error in coordinate selection, use popup to get information.
            coords, ok = QtWidgets.QInputDialog.getMultiLineText(
                self.window(),
                'Input coordinates',
                'Write one mode on each line, with its name (not index!) then '
                'either x, y, or value'
            )
            if not ok:
                raise ValueError('User cancelled operation')
        elif self.den2d_coord.ycoord is None:
            # this function currently only deals with 2d densities -- user
            # can use showd1d if they want 1d densities
            raise ValueError('A y coordinate was not selected')
        inp = ''
        # choose state (60), plot one state only (1)
        inp += f'60\n1\n{self.den2d_state.value()}\n'
        # choose coordinates (20)
        inp += f'20\n{coords}\n'
        # save data to xyz file (5), enter name, then exit (0)
        inp += '5\nden2d.xyz\n0'
        # run the command
        self.runCmd('showsys', '-nopes', input=inp)

        with open(filepath, mode='r', encoding='utf-8') as f:
            # this file essentially has xyz data for each time interval. there
            # are two empty lines between the data for each time interval.
            # annoyingly, one of the empty lines has whitespace in it, so we
            # can't simply match \n{3} -- have to match newline and possible
            # whitespace
            intervals = [self.readFloats(i.split('\n')) for i \
                         in re.split(r'(?:\n\s*){3}', f.read()) if i != '']
            # create list of 2d matrices for z, one for each time interval
            zt = []
            # for each interval, convert from list xyz coordinate data to grid
            # data
            for i, interval in enumerate(intervals):
                # assume x, y are same for each interval, so shape of z can be
                # inferred from the first pass
                if i == 0:
                    x = np.unique(interval[:, 0])
                    y = np.unique(interval[:, 1])
                zt.append(np.array(interval[:, 2]).reshape(x.shape[0], y.shape[0]))
        self.window().data = np.array(zt)

        # set contents of showsys.log to text view
        filepath = self.window().cwd/'showsys.log'
        if filepath.is_file():
            with open(filepath, mode='r', encoding='utf-8') as f:
                self.window().text.setPlainText(f'{"-"*80}\n{f.read()}')

        # adjust scrubber properties, connect to showd2dChangePlot slot
        self.window().scrubber.setMaximum(len(self.window().data)-1)
        self.window().scrubber.setSliderPosition(0)
        try:
            self.window().scrubber.valueChanged.disconnect()
        except TypeError:
            # happens if scrubber has no connections
            pass
        finally:
            self.window().scrubber.valueChanged.connect(self.showd2dChangePlot)
        self.window().graph.reset(switch_to_plot=True, animated=True)
        self.window().graph.setLabels(title='2D Density',
                                      bottom=f'DOF {self.den2d_coord.xcoord} (au)',
                                      left=f'DOF {self.den2d_coord.ycoord} (au)')
        levels = np.linspace(self.window().data.min(), self.window().data.max(), 21)
        self.window().graph.plotContours(x, y, self.window().data[0], levels)

    @QtCore.pyqtSlot()
    def showd2dChangePlot(self):
        '''
        Allows the user to move the scrubber to control time when using the
        showd2d analysis.
        '''
        scrubber_pos = int(self.window().scrubber.value())
        for isocurve in self.window().graph.getPlotItem().items:
            isocurve.setData(self.window().data[scrubber_pos])

    def showpes(self):
        '''
        Reads the xyz file from the menu-driven output of showsys -pes.
        The menu entries that are navigated by this function are:
            10 (choose task)
            20 (coordinate selection)
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
        filepath = self.window().cwd/'pes.xyz'
        filepath.unlink(missing_ok=True)

        coords = str(self.showpes_coord)
        if not coords:
            # error in coordinate selection, use popup to get information.
            coords, ok = QtWidgets.QInputDialog.getMultiLineText(
                self.window(),
                'Input coordinates',
                'Write one mode on each line, with its name (not index!) then '
                'either x, y, or value'
            )
            if not ok:
                raise ValueError('User cancelled operation')
        inp = ''
        # choose task (10)
        inp += {0: '10\n2\n', 1: '10\n1\n'}[self.showpes_type.currentIndex()]
        # choose state (60), plot one state only (1)
        inp += f'60\n1\n{self.showpes_state.value()}\n'
        # choose coordinates (20)
        inp += f'20\n{coords}\n'
        # save data to xyz file (5), enter name, then exit (0)
        inp += '5\npes.xyz\n0'
        # run the command
        self.runCmd('showsys', '-pes', input=inp)

        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f)
        # set contents of showsys.log to text view
        filepath = self.window().cwd/'showsys.log'
        if filepath.is_file():
            with open(filepath, mode='r', encoding='utf-8') as f:
                self.window().text.setPlainText(f'{"-"*80}\n{f.read()}')

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        if self.window().data.shape[1] == 3:
            # contour plot
            # convert from list xyz coordinate data to grid data
            x = np.unique(self.window().data[:, 0])
            y = np.unique(self.window().data[:, 1])
            z = np.array(self.window().data[:, 2]).reshape(x.shape[0], y.shape[0])
            self.window().graph.setLabels(title=self.showpes_type.currentText(),
                                          bottom=f'DOF {self.showpes_coord.xcoord} (au)',
                                          left=f'DOF {self.showpes_coord.ycoord} (au)')
            self.window().graph.plotContours(x, y, z, 21)
        else:
            # line plot
            self.window().graph.setLabels(title=self.showpes_type.currentText(),
                                          bottom=f'DOF {self.showpes_coord.xcoord} (au)',
                                          left='PES')
            self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 1],
                                     name='PES', pen='r')
