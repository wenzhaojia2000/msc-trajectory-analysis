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
        self.autocol_prefac = self.owner.findChild(QtWidgets.QComboBox, 'prefac_combobox')
        self.autocol_emin = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'emin_spinbox')
        self.autocol_emax = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'emax_spinbox')
        self.autocol_unit = self.owner.findChild(QtWidgets.QComboBox, 'unit_combobox')
        self.autocol_tau = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'tau_spinbox')
        self.autocol_iexp = self.owner.findChild(QtWidgets.QSpinBox, 'iexp_spinbox')
        # box is hidden initially
        self.autocol_box.hide()

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
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analres_1': # plot autocorrelation function
                self.rdauto()
            case 'analres_2': # plot spectrum from autocorrelation function
                self.autospec()
            case 'analres_3': # plot eigenvalues from matrix diagonalisation
                self.runCmd('rdeigval', '-inter')

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {1: self.autocol_box}
        for radio, box in options.items():
            if self.radio[radio].isChecked():
                box.show()
            else:
                box.hide()

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

    def autospec(self):
        '''
        Reads the command output of using autospec, which is expected to be in
        the format

        E.1    g0.1    g1.1    g2.1
        E.2    g0.2    g1.2    g2.2
        ...    ...     ...     ...
        E.m    g0.m    g1.m    g2.m

        where E is energy, and gn are the spectra of the various filter
        functions. Lines starting with '#' are ignored. Each cell should be in
        a numeric form that can be converted into a float like 0.123 or
        1.234E-10, etc., and cells are seperated with any number of spaces (or
        tabs).

        Plots the spectrum of the autocorrelation function.
        '''
        # map of autocol_unit indices to command line argument (labels are different)
        autocol_unit_map = {0: "ev", 1: "au", 2: "nmwl", 3: "cm-1", 4: "kcal/mol"}
        # additional arguments for autocorrelation options
        autocol_options = [
            str(self.autocol_emin.value()),
            str(self.autocol_emax.value()),
            autocol_unit_map[self.autocol_unit.currentIndex()],
            str(self.autocol_tau.value()),
            str(self.autocol_iexp.value())
        ]
        match self.autocol_prefac.currentIndex():
            case 0:
                output = self.runCmd('autospec', '-FT', *autocol_options)
            case 1:
                output = self.runCmd('autospec', '-EP', *autocol_options)
        if output is None:
            return None

        arr = []
        filepath = Path(self.owner.dir_edit.text())/'spectrum.pl'
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f:
                # ignore lines starting with #
                if line.startswith('#'):
                    continue
                # find all floats in the line
                matches = re.findall(self.float_regex, line)
                # should find 4 floats per line, if not, ignore that line
                if len(matches) != 4:
                    continue
                arr.append(list(map(float, matches)))
        if len(arr) == 0:
            # nothing found?
            print('[AnalysisResults.autospec] I wasn\'t given any values to plot')
            return None
        if self.owner.keep_files.isChecked() is False:
            # delete intermediate file
            filepath.unlink()
        self.owner.data = np.array(arr)
        self.owner.resetPlot(True)

        # start plotting
        self.owner.graph.setLabel('bottom', f'Energy ({self.autocol_unit.currentText()})', color='k')
        self.owner.graph.setLabel('left', 'Spectrum', color='k')
        self.owner.changePlotTitle('Autocorrelation spectrum')
        self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 1],
                              name='g0', pen='r')
        self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 2],
                              name='g1', pen='b')
        self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 3],
                              name='g2', pen='g')
        return None
