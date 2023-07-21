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
                    self.runCmd('checkdb')
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
        self.parent().text.setText("")
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
