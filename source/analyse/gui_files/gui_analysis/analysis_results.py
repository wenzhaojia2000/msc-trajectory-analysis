# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import re
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisResults(QtWidgets.QWidget, AnalysisTab):
    '''
    Defines functionality for the "Analyse Results" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analres_push',
                         box_name='analres_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box "autocorrelation options"
        self.autocol_box = self.owner.findChild(QtWidgets.QGroupBox, 'autocorrelation_box')
        self.autocol_emin = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'emin_spinbox')
        self.autocol_emax = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'emax_spinbox')
        self.autocol_unit = self.owner.findChild(QtWidgets.QComboBox, 'unit_combobox')
        self.autocol_tau = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'tau_spinbox')
        self.autocol_iexp = self.owner.findChild(QtWidgets.QSpinBox, 'iexp_spinbox')
        # box is hidden initially
        self.autocol_box.hide()
        # map of autocol_unit indices to command line argument (labels are different)
        self.autocol_unit_map = {0: "ev", 1: "au", 2: "nmwl", 3: "cm-1", 4: "kcal/mol"}

    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the autocorrelation box when certain result in analyse results
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)
        # in autocorrelation box, allow damping order to change if tau nonzero
        self.autocol_tau.valueChanged.connect(self.autocolDampingChanged)

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # additional arguments for autocorrelation options
        autocol_options = [
            str(self.autocol_emin.value()),
            str(self.autocol_emax.value()),
            self.autocol_unit_map[self.autocol_unit.currentIndex()],
            str(self.autocol_tau.value()),
            str(self.autocol_iexp.value())
        ]
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analres_1': # plot autocorrelation function
                self.rdauto()
            case 'analres_2': # plot FT of autocorrelation function
                self.runCmd('autospec', '-inter', '-FT', *autocol_options)
            case 'analres_3': # plot spectrum from autocorrelation function
                self.runCmd('autospec', '-inter', *autocol_options)
            case 'analres_4': # plot eigenvalues from matrix diagonalisation
                self.runCmd('rdeigval', '-inter')

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        if self.radio[1].isChecked() or self.radio[2].isChecked():
            self.autocol_box.show()
        else:
            self.autocol_box.hide()

    @QtCore.pyqtSlot()
    def autocolDampingChanged(self) -> None:
        '''
        Allows the user to change the damping order if the damping time is set
        to non-zero (ie. damping is enabled)
        '''
        if self.autocol_tau.value() == 0.0:
            self.autocol_iexp.setEnabled(False)
        else:
            self.autocol_iexp.setEnabled(True)
            
    def rdauto(self, plot_error:bool=False) -> None:
        '''
        Reads the auto file, which is expected to be in the format

        t.1    y1.1    y2.1    y3.1
        t.2    y1.2    y2.2    y3.2
        ...    ...     ...     ...
        t.m    y1.m    y2.m    y3.m

        where x is time, and y1, y2, y3 are the real, imaginary, and absolute
        value of the autocorrelation function. Headers are ignored. Each cell
        should be in a numeric form that can be converted into a float like
        0.123 or 1.234E-10, etc., and cells are seperated with any number of
        spaces (or tabs).

        Plots the autocorrelation function. Note that this function does not
        use the 'rdauto' command, as it essentially just prints out the auto
        file anyway.
        '''
        filepath = Path(self.owner.dir_edit.text())/'auto'
        if filepath.is_file() is False:
            self.owner.showError('FileNotFound: Cannot find auto file in directory')
            return None
        # reset text
        self.owner.text.setText("")
        # assemble data matrix
        arr = []
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f:
                # append line to text view (without \n at end)
                self.owner.text.append(line[:-1])
                # find all floats in the line
                matches = re.findall(self.float_regex, line)
                # should find four floats per line (t, y1, y2, y3)
                if len(matches) == 4:
                    # regex returns strings, need to convert into float
                    arr.append(list(map(float, matches)))
        if len(arr) == 0:
            # nothing found?
            print('[AnalysisResults.rdauto] I wasn\'t given any values to plot')
            return None
        self.owner.data = np.array(arr)
        self.owner.resetPlot(True)

        # start plotting
        self.owner.graph.setLabel('bottom', 'Time (fs)', color='k')
        self.owner.graph.setLabel('left', 'C(t)', color='k')
        self.owner.changePlotTitle('Autocorrelation function')
        self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 1],
                              name='Real autocorrelation function', pen='r')
        self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 2],
                              name='Imag. autocorrelation function', pen='b')
        self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 3],
                              name='Abs. autocorrelation function', pen='g')
        return None
