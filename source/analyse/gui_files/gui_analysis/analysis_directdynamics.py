# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import re
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisDirectDynamics(AnalysisTab):
    '''
    Defines functionality for the "Analyse Direct Dynamics" tab of the analysis
    GUI.
    '''
    def __init__(self, parent:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(parent=parent, push_name='analdd_push',
                         box_name='analdd_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'clean database options'
        self.clean_box = self.parent().findChild(QtWidgets.QGroupBox, 'clean_box')
        self.clean_testint = self.parent().findChild(QtWidgets.QCheckBox, 'clean_testint')
        self.clean_rmdup = self.parent().findChild(QtWidgets.QCheckBox, 'clean_rmdup')
        self.clean_mindb = self.parent().findChild(QtWidgets.QDoubleSpinBox, 'clean_mindb')
        self.clean_rmfail = self.parent().findChild(QtWidgets.QCheckBox, 'clean_rmfail')
        self.clean_rminterp = self.parent().findChild(QtWidgets.QCheckBox, 'clean_rminterp')
        # box is hidden initially
        self.clean_box.hide()

    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the update options box when certain result is selected
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)
        # in clean database box, show certain options only when checked
        self.clean_rmdup.stateChanged.connect(self.cleanOptionChanged)
        self.clean_rmfail.stateChanged.connect(self.cleanOptionChanged)

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {2: self.clean_box}
        for radio, box in options.items():
            if self.radio[radio].isChecked():
                box.show()
            else:
                box.hide()

    @QtCore.pyqtSlot()
    def cleanOptionChanged(self) -> None:
        '''
        Allows the user to change the duplicate removal tolerance if the remove
        duplicate box is checked, and the remove interpolated points checkbox
        if the remove failed points box is checked.
        '''
        self.clean_mindb.setEnabled(self.clean_rmdup.isChecked())
        self.clean_rminterp.setEnabled(self.clean_rmfail.isChecked())
        # uncheck box when disabled
        if self.clean_rminterp.isEnabled() is False:
            self.clean_rminterp.setChecked(False)

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
                case 'analdd_1': # plot calculation rate in log
                    self.calcrate()
                case 'analdd_2': # check database
                    raise NotImplementedError('Not implemented yet')
                case 'analdd_3':
                    self.checkdb()
                case 'analdd_4':
                    raise NotImplementedError('Not implemented yet')
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.parent().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.parent(), 'Error', f'{type(e).__name__}: {e}')

    def calcrate(self) -> None:
        '''
        Reads the log and looks for lines of the following format
        
        time[fs]       t1
        ...
        No. QC calculations :     N1.1
        ...
        No. QC calculations :     N1.n
        ... (etc)
        
        and plots the number of calculations per timestep against time.
        '''
        filepath = Path(self.parent().dir_edit.text())/'log'
        if filepath.is_file() is False:
            raise FileNotFoundError('Cannot find log file in directory')
        times = []
        n_calcs = []
        self.parent().text.setPlainText('')
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f:
                self.parent().text.append(line[:-1])
                # find a line with time[fs] in it and get time 
                if re.search(r'time\[fs\]', line):
                    try:
                        time = float(re.search(r'[+-]?\d+(?:\.\d*)?', line)[0])
                        times.append(time)
                        n_calcs.append(0)
                    except:
                        pass
                # find a line with No. QC calculations in it and get n_calc
                if re.search(r'No\. QC calculations :', line):
                    try:
                        n_calc = int(re.search(r'\d+', line)[0])
                        n_calcs[-1] += n_calc
                    except:
                        pass
        if len(times) == 0:
            # nothing found?
            raise ValueError('Invalid log file')
        self.parent().data = np.array([times, n_calcs])

        # start plotting, depending on options
        self.parent().resetPlot(True)
        self.parent().setPlotLabels(title='Calculations per time step',
                                    bottom='Time (fs)', left='QC calculations')
        self.parent().graph.plot(self.parent().data[0, :], self.parent().data[1, :],
                                 name='QC calculations', pen='r')

    def checkdb(self) -> None:
        '''
        Executes the checkdb command with options depending on which options
        the user has chosen.
        '''
        clean_options = []
        if self.clean_testint.isChecked():
            clean_options.append('-rd')
        if self.clean_rmdup.isChecked():
            clean_options.append('-d')
            clean_options.append('-mindb ' + str(self.clean_mindb.value()))
        if self.clean_rminterp.isChecked():
            clean_options.append('-sc')
        elif self.clean_rmfail.isChecked():
            clean_options.append('-c')
        # switch to text view to see output
        self.parent().tab_widget.setCurrentIndex(0)
        self.runCmd('checkdb', *clean_options)
