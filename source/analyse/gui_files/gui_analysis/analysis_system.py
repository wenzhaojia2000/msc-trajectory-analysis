# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import re
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisSystem(QtWidgets.QWidget, AnalysisTab):
    '''
    Defines functionality for the "Analyse System Evolution" tab of the
    analysis GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analsys_push',
                         box_name='analsys_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        self.den1d_box = self.owner.findChild(QtWidgets.QGroupBox, 'den1d_box')
        self.dof = self.owner.findChild(QtWidgets.QSpinBox, 'dof_spinbox')
        self.state = self.owner.findChild(QtWidgets.QSpinBox, 'state_spinbox')

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
        match radio_name:
            case 'analsys_1': # plot 1d density evolution
                # self.runCmd('showd1d', '-inter', input='1')
                self.showd1d()
            case 'analsys_2': # plot 2d density evolution
                self.runCmd('showsys')
            case 'analsys_3': # plot diabatic state population
                self.runCmd('plstate')
            case 'analsys_4': # plot potential energy surface
                self.runCmd('showsys', '-pes', input='1')

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
        in the format

        x.11    t.1    y1.11    y2.11
        x.12    t.1    y1.12    y2.12
        ...     ...    ...      ...
        x.1n    t.1    y1.1n    y2.1n
                                         <- empty line
        x.21    t.2    y1.21    y2.21
        ...     ...    ...      ...
        x.2n    t.2    y1.2n    y2.2n
        ...                              <- empty lines
        x.mn    t.m    y1.mn    y2.mn
                                         <- empty line(s) at end of file

        where x is position, t is time, and y1, y2 are the real and imag parts
        of the spf (?). Any lines starting with "set" or "plot" are ignored.
        Time intervals t.1 ... t.m are expected to increase linearly upwards.
        Each cell should be in a numeric form that can be converted into a
        float like 0.123 or 1.234E-10, etc., and cells are seperated with any
        number of spaces (or tabs).

        Plots the density over position with a scroll bar to scroll through
        time.
        '''
        den1d_options = [
            'f' + str(self.dof.value()),
            's' + str(self.state.value())
        ]
        output = self.runCmd('showd1d', '-T', '-w', *den1d_options)
        if output is None:
            return None

        # find filename of command output
        if self.state.value() == 1:
            filepath = Path(self.owner.dir_edit.text())/f'den1d_{den1d_options[0]}'
        else:
            filepath = Path(self.owner.dir_edit.text())/f'den1d_{"_".join(den1d_options)}'
        # arr is the entire data array, consisting of blocks, a compoent of arr
        # which represents the values at one given time.
        arr = []
        block = []
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f:
                # ignore lines starting with set or plot
                if line.startswith('set') or line.startswith('plot'):
                    continue
                # new line. add block to arr and start a new block
                if line == "\n":
                    block = np.array(block)
                    if block.size != 0:
                        arr.append(block)
                    block = []
                    continue
                # find all floats in the line
                matches = re.findall(self.float_regex, line)
                # should find 4 floats per line, if not, ignore that line
                if len(matches) != 4:
                    continue
                block.append(list(map(float, matches)))
        if len(arr) == 0:
            # nothing found?
            print('[AnalysisIntegrator.showd1d] I wasn\'t given any values to plot')
            return None
        self.owner.data = arr
        self.owner.resetPlot(True)

        # show slider and save video option, set max value, and plot depending
        # on position
        self.owner.save_video.setVisible(True)
        self.owner.slider.show()
        self.owner.slider.setMaximum(len(self.owner.data)-1)
        self.owner.slider.setSliderPosition(0)
        try:
            self.owner.slider.sliderMoved.disconnect()
        except TypeError:
            # happens if slider has no connections
            pass
        finally:
            self.owner.slider.sliderMoved.connect(self.showd1dChangePlot)
        # start plotting
        self.owner.changePlotTitle('1D density evolution')
        self.owner.graph.setLabel('bottom', 'x', color='k')
        self.owner.graph.setLabel('left', 'y', color='k')
        self.owner.graph.plot(self.owner.data[0][:, 0], self.owner.data[0][:, 2],
                              name='Re(phi)', pen='r')
        self.owner.graph.plot(self.owner.data[0][:, 0], self.owner.data[0][:, 3],
                              name='Im(phi)', pen='b')
        return None
    
    @QtCore.pyqtSlot()
    def showd1dChangePlot(self) -> None:
        '''
        Allows the user to move the slider to control time when using the
        showd1d analysis.
        '''
        data_items = self.owner.graph.listDataItems()
        slider_pos = int(self.owner.slider.value())
        if self.owner.data and len(data_items) == 2:
            re, im = data_items
            if re.name() == 'Re(phi)' and im.name() == 'Im(phi)':
                re.setData(self.owner.data[slider_pos][:, 0],
                           self.owner.data[slider_pos][:, 2])
                im.setData(self.owner.data[slider_pos][:, 0],
                           self.owner.data[slider_pos][:, 3])
        return None
