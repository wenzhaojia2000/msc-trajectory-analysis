# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import re
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import BarGraphItem
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisIntegrator(QtWidgets.QWidget, AnalysisTab):
    '''
    Defines functionality for the "Analyse Integrator" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analint_push',
                         box_name='analint_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        self.timing_box = self.owner.findChild(QtWidgets.QGroupBox, 'timing_box')
        self.timing_sort = self.owner.findChild(QtWidgets.QComboBox, 'timing_combobox')
        # box is hidden initially
        self.timing_box.hide()

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
            case 'analint_1': # analyse step size
                self.runCmd('rdsteps')
            case 'analint_2': # look at timing file
                self.rdtiming()
            case 'analint_3': # plot update file step size
                self.rdupdate(plot_error=False)
            case 'analint_4': # plot update file errors
                self.rdupdate(plot_error=True)

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {1: self.timing_box}
        for radio, box in options.items():
            if self.radio[radio].isChecked():
                box.show()
            else:
                box.hide()

    def rdtiming(self) -> None:
        '''
        Reads the timing file, which is expected to be in the format

        [host, time, directory information]
        Subroutine  Calls N  cpu/N    cpu      %cpu     Clock
        name.1      a.1      b.1      c.1      d.1      e.1
        name.2      a.2      b.2      c.2      d.2      e.2
        ...         ...      ...      ...      ...      ...
        name.m      a.m      b.m      c.m      d.m      e.m

        Total ...
        [any other information]

        name should be a string *with no spaces*, as cells should be seperated
        by spaces. The other cells should be in a numeric form that can be
        converted into a float like 0.123 or 1.234E-10, etc.

        Plots a bar graph of the column selected by the user, and also outputs
        the timing file sorted by the selected column in the text tab.
        '''
        filepath = Path(self.owner.dir_edit.text())/'timing'
        if filepath.is_file() is False:
            self.owner.showError('FileNotFound: Cannot find timing file in directory')
            return None
        with open(filepath, mode='r', encoding='utf-8') as f:
            text = f.read()
        # split after 'Clock' and before 'Total' (see docstring), so we have
        # three strings, with the middle being the data
        splits = re.split(r'(?<=Clock)\n|\n(?=Total)', text, flags=re.IGNORECASE)
        if len(splits) != 3:
            self.owner.showError('ValueError: Invalid timing file')
            return None
        pre, text, post = splits

        arr = []
        for line in text.split('\n'):
            # should find one name and five floats per line (name, a, b, c, d,
            # e). need to use findall instead of search/match to return just
            # the part in the brackets
            name = re.findall(r'^ *(\S+)', line)
            floats = re.findall(self.float_regex, line)
            if len(name) == 1 and len(floats) == 5:
                # regex returns strings, need to convert into float. the last
                # entry is the line itself, which is already formatted in a
                # nice way. this saves manually formatting the data
                arr.append(tuple(name + list(map(float, floats)) + [line]))
        if len(arr) == 0:
            # nothing found?
            self.owner.showError('ValueError: Invalid timing file')
            return None

        # sort by column chosen by user
        if self.timing_sort.currentIndex() == 0:
            # sort by name
            arr.sort(key=lambda x: x[0])
        else:
            # sort by number (largest first)
            arr.sort(key=lambda x: -x[self.timing_sort.currentIndex()])
        self.owner.data = arr

        # display sorted text
        text = "\n".join([line[-1] for line in self.owner.data])
        self.owner.text.setText(f'{pre}\n{text}\n\n{post}')
        self.owner.resetPlot()

        # start plotting
        self.owner.changePlotTitle('Subroutine timings')
        self.owner.graph.setLabel('left', '')
        # this is a horizontal bar chart so everything is spun 90 deg. can't
        # do a normal vertical one as pyqtgraph can't rotate tick names (yet)
        if self.timing_sort.currentIndex() == 0:
            # plot cpu if 'name' is selected (names don't have values)
            values = [row[3] for row in self.owner.data]
            self.owner.graph.setLabel('bottom', 'CPU', color='k')
        else:
            values = [row[self.timing_sort.currentIndex()] for row in self.owner.data]
            self.owner.graph.setLabel('bottom', self.timing_sort.currentText(), color='k')
        names = [row[0] for row in self.owner.data]
        positions = list(range(1, len(values)+1))
        bar = BarGraphItem(x0=0, y=positions, height=0.6, width=values)
        self.owner.graph.addItem(bar)
        # sort out bar chart ticks https://stackoverflow.com/questions/72002352
        ticks = []
        for i, label in enumerate(names):
            ticks.append((positions[i], label))
        self.owner.graph.getAxis('left').setTicks([ticks])
        return None

    def rdupdate(self, plot_error:bool=False) -> None:
        '''
        Reads the command output of using rdupdate, which is expected to be in
        the format, where each cell is a float,

        t.1    y1.1    y2.1    y3.1
        t.2    y1.2    y2.2    y3.2
        ...    ...     ...     ...
        t.m    y1.m    y2.m    y3.m

        where t is time, y1 is step size, y2 is error of A, y3 is error of phi.

        Plots the step size is plot_error is false, otherwise plots the errors,
        chosen by the self.update_plot combobox.
        '''
        output = self.runCmd('rdupdate')
        if output is None:
            return None
        # assemble data matrix
        self.readFloats(output.split('\n'), 4)

        # start plotting, depending on options
        self.owner.resetPlot(True)
        if plot_error:
            self.owner.setPlotLabels(title='Update file errors',
                                     bottom='Time (fs)', left='Error')
            self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 2],
                                  name='Error of A-vector', pen='r')
            self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 3],
                                  name='Error of SPFs', pen='b')
        else:
            self.owner.setPlotLabels(title='Update file step size',
                                     bottom='Time (fs)', left='Step size (fs)')
            self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 1],
                                  name='Step size', pen='r')
        return None
