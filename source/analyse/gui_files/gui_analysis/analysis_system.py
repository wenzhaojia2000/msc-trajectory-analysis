# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisSystem(AnalysisTab):
    '''
    Defines functionality for the "Analyse System Evolution" tab of the
    analysis GUI.
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
        self.den1d_box = self.parent().findChild(QtWidgets.QGroupBox, 'den1d_box')
        self.dof = self.parent().findChild(QtWidgets.QSpinBox, 'dof_spinbox')
        self.state = self.parent().findChild(QtWidgets.QSpinBox, 'state_spinbox')

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
                    self.runCmd('showsys', '-pes', input='1')
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.parent().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.parent(), 'Error', f'{type(e).__name__}: {e}')

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {0: self.den1d_box}
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
            'f' + str(self.dof.value()),
            's' + str(self.state.value())
        ]
        self.runCmd('showd1d', '-T', '-w', *den1d_options)

        # find filename of command output
        if self.state.value() == 1:
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
                self.parent().text.append(f'{"-"*80}\n{f.read()}')
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
                                    bottom='rd (au)', left='V (ev)',
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
