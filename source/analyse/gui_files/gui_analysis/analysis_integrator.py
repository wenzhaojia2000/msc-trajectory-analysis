# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import re
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import BarGraphItem
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisIntegrator(AnalysisTab):
    '''
    Defines functionality for the "Analyse Integrator" tab of the analysis
    GUI.
    '''
    def __init__(self, parent:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(parent=parent, push_name='analint_push',
                         box_name='analint_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        self.timing_box = self.parent().findChild(QtWidgets.QGroupBox, 'timing_box')
        self.timing_sort = self.parent().findChild(QtWidgets.QComboBox, 'timing_combobox')
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
        try:
            match radio_name:
                case 'analint_1': # analyse step size
                    self.runCmd('rdsteps')
                case 'analint_2': # look at timing file
                    self.rdtiming()
                case 'analint_3': # plot update file step size
                    self.rdupdate(plot_error=False)
                case 'analint_4': # plot update file errors
                    self.rdupdate(plot_error=True)
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.parent().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.parent(), 'Error', f'{type(e).__name__}: {e}')

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

        name should be a string, and other cells should be in a numeric form
        that can be converted into a float like 0.123 or 1.234E-10, etc.

        Plots a bar graph of the column selected by the user, and also outputs
        the timing file sorted by the selected column in the text tab.
        '''
        filepath = Path(self.parent().dir_edit.text())/'timing'
        if filepath.is_file() is False:
            raise FileNotFoundError('Cannot find timing file in directory')
        with open(filepath, mode='r', encoding='utf-8') as f:
            text = f.read()
        # split after 'Clock' and before 'Total' (see docstring), so we have
        # three strings, with the middle being the data
        splits = re.split(r'(?<=Clock)\n|\n(?=Total)', text, flags=re.IGNORECASE)
        if len(splits) != 3:
            raise ValueError('Invalid timing file')
        pre, text, post = splits

        arr = []
        for line in text.split('\n'):
            # should find one name and five floats per line (name, a, b, c, d,
            # e). after splitting by whitespace, floats should take up the last
            # 5 entries, and the name take up the rest
            row = re.findall(r'\S+', line)
            if len(row) >= 5:
                name = ' '.join(row[:-5])
                floats = row[-5:]
                # floats are still strings, need to convert. the last entry is
                # the line itself, which is already formatted in a nice way.
                # this saves manually formatting the data
                arr.append(tuple([name] + list(map(float, floats)) + [line]))
        if len(arr) == 0:
            # nothing found?
            raise ValueError('Invalid timing file')

        # sort by column chosen by user
        if self.timing_sort.currentIndex() == 0:
            # sort by name
            arr.sort(key=lambda x: x[0])
        else:
            # sort by number (largest first)
            arr.sort(key=lambda x: -x[self.timing_sort.currentIndex()])
        self.parent().data = arr

        # display sorted text
        text = "\n".join([line[-1] for line in self.parent().data])
        self.parent().text.setText(f'{pre}\n{text}\n\n{post}')
        self.parent().resetPlot()

        # start plotting
        self.parent().setPlotLabels(title='Subroutine timings', left='')
        # this is a horizontal bar chart so everything is spun 90 deg. can't
        # do a normal vertical one as pyqtgraph can't rotate tick names (yet)
        if self.timing_sort.currentIndex() == 0:
            # plot cpu if 'name' is selected (names don't have values)
            values = [row[3] for row in self.parent().data]
            self.parent().setPlotLabels(bottom='CPU')
        else:
            values = [row[self.timing_sort.currentIndex()] for row in self.parent().data]
            self.parent().setPlotLabels(bottom=self.timing_sort.currentText())
        names = [row[0] for row in self.parent().data]
        positions = list(range(1, len(values)+1))
        bar = BarGraphItem(x0=0, y=positions, height=0.6, width=values)
        self.parent().graph.addItem(bar)
        # sort out bar chart ticks https://stackoverflow.com/questions/72002352
        ticks = []
        for i, label in enumerate(names):
            ticks.append((positions[i], label))
        self.parent().graph.getAxis('left').setTicks([ticks])

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
        # assemble data matrix
        self.readFloats(output.split('\n'), 4)

        # start plotting, depending on options
        self.parent().resetPlot(True)
        if plot_error:
            self.parent().setPlotLabels(title='Update file errors',
                                        bottom='Time (fs)', left='Error')
            self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 2],
                                     name='Error of A-vector', pen='r')
            self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 3],
                                     name='Error of SPFs', pen='b')
        else:
            self.parent().setPlotLabels(title='Update file step size',
                                        bottom='Time (fs)', left='Step size (fs)')
            self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 1],
                                     name='Step size', pen='r')
